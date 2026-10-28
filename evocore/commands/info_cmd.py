"""info_cmd.py — CLI command for inspecting EvoCore appliance environment and runtime telemetry."""
from __future__ import annotations

from pathlib import Path
import click

from evocore.constants import DEFAULT_BASE_ISO, VERSION
from evocore.core.profile import ProfileManager
from evocore.utils.output import common_cli_options, sync_output_formatter
from evocore.utils.qemu import find_qemu


@click.command("info", help="Display EvoCore appliance environment, QEMU status, and build artifacts.")
@common_cli_options
@click.pass_context
def info_cmd(ctx: click.Context, json_mode: bool, quiet: bool, verbose: bool) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    root = Path(__file__).resolve().parent.parent.parent

    qemu_info = find_qemu()
    base_iso = root / DEFAULT_BASE_ISO
    pm = ProfileManager(root / "profiles")
    profiles = pm.list_profiles()

    out_dir = root / "output"
    artifacts: dict[str, bool] = {}
    if out_dir.is_dir():
        for p in profiles:
            p_name = p["name"]
            p_out = out_dir / p_name
            artifacts[f"{p_name}_kernel"] = (p_out / "boot" / "vmlinuz").is_file()
            artifacts[f"{p_name}_initrd"] = (p_out / "boot" / "core.gz").is_file()
            artifacts[f"{p_name}_iso"] = (p_out / f"EvoCore-{p_name}.iso").is_file()

    info_data = {
        "appliance": "EvoCore",
        "version": VERSION,
        "root_directory": str(root),
        "qemu": {
            "available": qemu_info.available,
            "path": str(qemu_info.path) if qemu_info.path else None,
            "version": qemu_info.version,
            "target_arch": qemu_info.target_arch,
        },
        "base_iso": {
            "path": str(base_iso),
            "present": base_iso.is_file(),
            "size_mb": round(base_iso.stat().st_size / (1024 * 1024), 2) if base_iso.is_file() else None,
        },
        "profiles": [p["name"] for p in profiles],
        "built_artifacts": artifacts,
    }

    if not formatter.json_mode:
        formatter.print_table(
            f"EvoCore Appliance Telemetry (v{VERSION})",
            [
                ("Root Directory", str(root)),
                ("QEMU Available", str(qemu_info.available)),
                ("QEMU Path", str(qemu_info.path) if qemu_info.path else "Not Found"),
                ("QEMU Version", qemu_info.version or "N/A"),
                ("Base ISO Present", f"{base_iso.is_file()} ({info_data['base_iso']['size_mb']} MB)" if base_iso.is_file() else "No"),
                ("Available Profiles", ", ".join(info_data["profiles"])),
            ],
        )

    formatter.emit_success(info_data)
