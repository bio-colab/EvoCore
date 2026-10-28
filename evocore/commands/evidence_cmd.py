"""evidence_cmd.py — CLI commands for auditing, verifying, and packaging scientific evidence."""
from __future__ import annotations

import json
from pathlib import Path
import click

from evocore.constants import (
    DEFAULT_BUNDLE_EXTENSION,
    EXIT_ATTESTATION_FAILED,
    EXIT_ERROR,
    EXIT_SUCCESS,
)
from evocore.core.bundle import EvidenceBundle
from evocore.core.provenance import verify_evidence_manifest
from evocore.utils.exceptions import EvoCoreArtifactNotFoundError, EvoCoreAttestationError, EvoCoreError
from evocore.utils.output import common_cli_options, sync_output_formatter


@click.group("evidence", help="Inspect, forensically audit, and package cryptographic evidence manifests.")
def evidence_group() -> None:
    pass


@evidence_group.command("verify", help="Forensically verify cryptographic integrity and Merkle proofs of evidence.")
@click.argument("target", type=click.Path(exists=True))
@click.option("--kernel", "-k", type=click.Path(exists=True), default=None, help="Kernel binary to cross-verify.")
@click.option("--initrd", "-i", type=click.Path(exists=True), default=None, help="Initramfs binary to cross-verify.")
@common_cli_options
@click.pass_context
def verify_cmd(
    ctx: click.Context,
    target: str,
    kernel: str | None,
    initrd: str | None,
    json_mode: bool,
    quiet: bool,
    verbose: bool,
) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    t_path = Path(target)

    try:
        if t_path.name.endswith(DEFAULT_BUNDLE_EXTENSION) or t_path.name.endswith(".tar.gz"):
            res = EvidenceBundle.verify(t_path)
        else:
            manifest = json.loads(t_path.read_text(encoding="utf-8"))
            res = verify_evidence_manifest(manifest, kernel_path=kernel, initrd_path=initrd)
            res["target_path"] = str(t_path)

        valid = res.get("valid", False)
        tampered = res.get("tampered_fields", [])

        if not formatter.json_mode:
            status_str = "AUTHENTIC & VERIFIED" if valid else "TAMPERED / CORRUPTED"
            formatter.print_table(
                f"EvoCore Cryptographic Verification: [{status_str}]",
                [
                    ("Target Path", str(t_path)),
                    ("Status", "[PASS]" if valid else "[FAIL]"),
                    ("Tampered Fields", ", ".join(tampered) if tampered else "None"),
                    ("Appliance", res.get("appliance", "EvoCore")),
                    ("Version", res.get("version", "unknown")),
                ],
            )

        if valid:
            formatter.emit_success(res, message="Cryptographic evidence verification PASSED.")
        else:
            formatter.emit_error(
                f"Evidence attestation FAILED! Tampered fields: {tampered}",
                exit_code=EXIT_ATTESTATION_FAILED,
                details=res,
            )
            ctx.exit(EXIT_ATTESTATION_FAILED)

    except EvoCoreError as exc:
        formatter.emit_error(exc.message, exit_code=exc.exit_code, details=exc.details)
        ctx.exit(exc.exit_code)
    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)


@evidence_group.command("inspect", help="Inspect contents and metrics of an evidence manifest or bundle.")
@click.argument("target", type=click.Path(exists=True))
@common_cli_options
@click.pass_context
def inspect_cmd(ctx: click.Context, target: str, json_mode: bool, quiet: bool, verbose: bool) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    t_path = Path(target)

    try:
        if t_path.name.endswith(DEFAULT_BUNDLE_EXTENSION) or t_path.name.endswith(".tar.gz"):
            data = EvidenceBundle.inspect(t_path)
        else:
            data = json.loads(t_path.read_text(encoding="utf-8"))

        if not formatter.json_mode:
            manifest = data.get("manifest", data)
            sol = manifest.get("solution", {})
            formatter.print_table(
                "Evidence Manifest Overview",
                [
                    ("Appliance", manifest.get("appliance", "N/A")),
                    ("Version", manifest.get("appliance_version", manifest.get("version", "N/A"))),
                    ("Timestamp (UTC)", manifest.get("timestamp_utc", "N/A")),
                    ("Formula", sol.get("expression", "N/A")),
                    ("Fitness", f"{sol.get('fitness_score', 0):.4f}"),
                    ("Passed Gates", str(sol.get("passed_gates"))),
                ],
            )
        formatter.emit_success(data)

    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)


@evidence_group.command("bundle", help="Pack evidence manifest, logs, and cryptographic proofs into sealed .evobundle.")
@click.argument("manifest_path", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(exists=False), help="Path for generated .evobundle.")
@click.option("--log", "-l", type=click.Path(exists=True), default=None, help="Optional raw serial execution log.")
@common_cli_options
@click.pass_context
def bundle_cmd(
    ctx: click.Context,
    manifest_path: str,
    output: str,
    log: str | None,
    json_mode: bool,
    quiet: bool,
    verbose: bool,
) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)

    try:
        m_data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        l_text = Path(log).read_text(encoding="utf-8", errors="replace") if log else None
        bundle_out = EvidenceBundle.pack(manifest_data=m_data, output_path=output, log_text=l_text)

        data = {
            "bundle_path": str(bundle_out),
            "bundle_size_bytes": bundle_out.stat().st_size,
        }
        formatter.emit_success(data, message=f"Sealed evidence bundle created: {bundle_out}")

    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)


@evidence_group.command("unpack", help="Unpack a sealed .evobundle archive into destination directory.")
@click.argument("bundle_path", type=click.Path(exists=True))
@click.option("--dest", "-d", required=True, type=click.Path(exists=False), help="Destination directory.")
@common_cli_options
@click.pass_context
def unpack_cmd(ctx: click.Context, bundle_path: str, dest: str, json_mode: bool, quiet: bool, verbose: bool) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)

    try:
        files = EvidenceBundle.unpack(bundle_path=bundle_path, destination_dir=dest)
        data = {
            "destination": dest,
            "extracted_count": len(files),
            "files": files,
        }
        formatter.emit_success(data, message=f"Extracted {len(files)} files to {dest}")

    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)
