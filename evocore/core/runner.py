"""runner.py — High-fidelity QEMU execution engine and evidence harvester for EvoCore."""
from __future__ import annotations

import dataclasses
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from evocore.constants import (
    DEFAULT_MANIFEST_NAME,
    DEFAULT_PROFILE,
    EXIT_ARTIFACT_NOT_FOUND,
    EXIT_QEMU_NOT_FOUND,
    EXIT_SUCCESS,
    EXIT_TIMEOUT,
)
from evocore.core.bundle import EvidenceBundle
from evocore.core.provenance import verify_evidence_manifest
from evocore.utils.exceptions import (
    EvoCoreArtifactNotFoundError,
    EvoCoreQemuNotFoundError,
    EvoCoreTimeoutError,
)
from evocore.utils.qemu import find_qemu


@dataclasses.dataclass
class RunResult:
    success: bool
    mode: str
    exit_code: int
    duration_seconds: float
    output_dir: str
    manifest: dict[str, Any] | None = None
    manifest_path: str | None = None
    bundle_path: str | None = None
    log_path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "mode": self.mode,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "output_dir": self.output_dir,
            "manifest": self.manifest,
            "manifest_path": self.manifest_path,
            "bundle_path": self.bundle_path,
            "log_path": self.log_path,
            "error": self.error,
        }


def extract_manifest_from_log(log_path: Path | str) -> dict[str, Any] | None:
    """Parses cryptographic evidence manifest block emitted by supervisor over serial line."""
    p = Path(log_path)
    if not p.is_file():
        return None

    text = p.read_text(encoding="utf-8", errors="replace")
    start_tag = "=== BEGIN EVOCORE EVIDENCE MANIFEST ==="
    end_tag = "=== END EVOCORE EVIDENCE MANIFEST ==="
    s_idx = text.find(start_tag)
    e_idx = text.find(end_tag)
    if s_idx == -1 or e_idx == -1:
        return None

    json_str = text[s_idx + len(start_tag) : e_idx].strip()
    try:
        return json.loads(json_str)
    except Exception:
        return None


class EvoRunner:
    """Orchestrates appliance boot in QEMU, captures output, and audits results."""

    def __init__(self, appliance_root: Path | str | None = None):
        if appliance_root:
            self.root = Path(appliance_root)
        else:
            self.root = Path(__file__).resolve().parent.parent.parent

    def run(
        self,
        mode: str = "lab",
        profile: str = DEFAULT_PROFILE,
        headless: bool = True,
        timeout: int = 90,
        memory_mb: int = 512,
        create_bundle: bool = False,
        output_dir: Path | str | None = None,
        extra_kernel_args: str = "",
    ) -> RunResult:
        """Boots EvoCore kernel & initramfs in QEMU, executing the scientific workflow."""
        t0 = time.time()
        qemu_info = find_qemu()
        if not qemu_info.available or not qemu_info.path:
            raise EvoCoreQemuNotFoundError(
                "QEMU x86_64 emulator was not found on this system. Install QEMU or set EVOCORE_QEMU_PATH."
            )

        prof_out = self.root / "output" / profile
        vmlinuz = prof_out / "boot" / "vmlinuz"
        core_gz = prof_out / "boot" / "core.gz"
        iso_path = prof_out / f"EvoCore-{profile}.iso"

        if mode == "iso":
            if not iso_path.is_file():
                raise EvoCoreArtifactNotFoundError(f"ISO image not found at {iso_path}. Run 'evocore build' first.")
        else:
            if not vmlinuz.is_file() or not core_gz.is_file():
                raise EvoCoreArtifactNotFoundError(
                    f"Appliance boot files not found in {prof_out / 'boot'}. Run 'evocore build --profile {profile}' first."
                )

        run_out = Path(output_dir or (self.root / "output"))
        run_out.mkdir(parents=True, exist_ok=True)
        log_file = run_out / "last_run.log"
        manifest_file = run_out / DEFAULT_MANIFEST_NAME

        # Assemble QEMU execution arguments
        cmd: list[str] = [str(qemu_info.path), "-m", f"{memory_mb}M"]

        if mode == "iso":
            cmd.extend([
                "-cdrom", str(iso_path),
                "-boot", "d",
                "-name", f"Darwin-Evolab EvoCore [ISO Boot: {profile}]",
            ])
            if headless:
                cmd.extend(["-nographic"])
        else:
            # Direct kernel + initramfs boot
            kernel_params = f"quiet evomode={mode}"
            if headless:
                kernel_params += " evopoweroff=1 console=ttyS0"
            else:
                kernel_params += " console=tty0"

            if extra_kernel_args:
                kernel_params += f" {extra_kernel_args}"

            cmd.extend([
                "-kernel", str(vmlinuz),
                "-initrd", str(core_gz),
                "-append", kernel_params,
                "-name", f"Darwin-Evolab EvoCore [{mode.upper()} Mode: {profile}]",
            ])

            if headless:
                cmd.extend([
                    "-serial", f"file:{log_file}",
                    "-nographic",
                ])

        # Execute
        if not headless:
            # Spawn interactive GUI subprocess
            proc = subprocess.Popen(cmd)
            return RunResult(
                success=True,
                mode=mode,
                exit_code=0,
                duration_seconds=round(time.time() - t0, 2),
                output_dir=str(run_out),
                log_path=None,
            )

        # Headless synchronous run with timeout
        try:
            res = subprocess.run(cmd, timeout=timeout, capture_output=True)
            duration = round(time.time() - t0, 2)
        except subprocess.TimeoutExpired:
            duration = round(time.time() - t0, 2)
            raise EvoCoreTimeoutError(
                f"EvoCore execution timed out after {timeout} seconds.",
                details={"timeout": timeout, "duration": duration, "mode": mode},
            )

        # Parse extracted manifest
        manifest_data = extract_manifest_from_log(log_file)
        bundle_path_str = None

        if manifest_data:
            manifest_file.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

            if create_bundle:
                bundle_path = run_out / f"experiment_{int(time.time())}.evobundle"
                log_content = log_file.read_text(encoding="utf-8", errors="replace") if log_file.is_file() else None
                EvidenceBundle.pack(
                    manifest_data=manifest_data,
                    output_path=bundle_path,
                    log_text=log_content,
                )
                bundle_path_str = str(bundle_path)

        return RunResult(
            success=(manifest_data is not None) if (mode == "lab" and headless) else True,
            mode=mode,
            exit_code=0,
            duration_seconds=duration,
            output_dir=str(run_out),
            manifest=manifest_data,
            manifest_path=str(manifest_file) if manifest_data else None,
            bundle_path=bundle_path_str,
            log_path=str(log_file) if log_file.is_file() else None,
        )
