"""qemu.py — Cross-platform QEMU hypervisor discovery and telemetry."""
from __future__ import annotations

import dataclasses
import os
import shutil
import subprocess
from pathlib import Path

from evocore.constants import QEMU_CANDIDATE_PATHS


@dataclasses.dataclass
class QemuInfo:
    available: bool
    path: Path | None = None
    version: str | None = None
    target_arch: str = "x86_64"


def find_qemu() -> QemuInfo:
    """Discovers installed QEMU x86_64 emulator on the system."""
    custom_env = os.environ.get("EVOCORE_QEMU_PATH") or os.environ.get("QEMU_PATH")
    if custom_env and Path(custom_env).is_file():
        return _inspect_qemu(Path(custom_env))

    which_path = shutil.which("qemu-system-x86_64")
    if which_path and Path(which_path).is_file():
        return _inspect_qemu(Path(which_path))

    for candidate in QEMU_CANDIDATE_PATHS:
        p = Path(candidate)
        if p.is_file():
            return _inspect_qemu(p)

    return QemuInfo(available=False)


def _inspect_qemu(qemu_path: Path) -> QemuInfo:
    version = None
    try:
        proc = subprocess.run(
            [str(qemu_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            first_line = proc.stdout.splitlines()[0] if proc.stdout else ""
            version = first_line.strip()
    except Exception:
        pass

    return QemuInfo(
        available=True,
        path=qemu_path.resolve(),
        version=version,
        target_arch="x86_64",
    )
