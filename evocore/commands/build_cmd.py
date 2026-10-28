"""build_cmd.py — CLI command for building and remastering EvoCore appliances."""
from __future__ import annotations

from pathlib import Path
import click

from evocore.constants import DEFAULT_PROFILE, EXIT_BUILD_FAILED, EXIT_SUCCESS
from evocore.core.forge import EvoForge
from evocore.utils.exceptions import EvoCoreError
from evocore.utils.output import common_cli_options, sync_output_formatter


@click.command("build", help="Build remastered EvoCore appliance ISO and initramfs from profile.")
@click.option("--profile", "-p", default=DEFAULT_PROFILE, help="Profile configuration name (default: minimal).")
@click.option("--base-iso", "-b", type=click.Path(exists=False), default=None, help="Base ISO image path.")
@click.option("--output-dir", "-o", type=click.Path(exists=False), default=None, help="Destination directory.")
@common_cli_options
@click.pass_context
def build_cmd(
    ctx: click.Context,
    profile: str,
    base_iso: str | None,
    output_dir: str | None,
    json_mode: bool,
    quiet: bool,
    verbose: bool,
) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    formatter.print_info(f"Initiating appliance build for profile: '{profile}'...")

    try:
        forge = EvoForge()
        manifest = forge.build_profile(
            profile_name=profile,
            base_iso=base_iso,
            output_dir=output_dir,
        )

        arts = manifest.get("artifacts", {})
        data = {
            "profile": profile,
            "version": manifest.get("version"),
            "build_duration_seconds": manifest.get("build_duration_seconds"),
            "output_directory": manifest.get("output_directory"),
            "artifacts": {
                "kernel_sha256": arts.get("vmlinuz_sha256"),
                "initrd_sha256": arts.get("initrd_sha256"),
                "initrd_size_bytes": arts.get("initrd_size"),
                "rootfs_merkle_root": arts.get("rootfs_merkle_root"),
                "iso_path": arts.get("iso_path"),
                "iso_sha256": arts.get("iso_sha256"),
                "composite_signature": arts.get("composite_signature"),
            },
        }

        if not formatter.json_mode:
            formatter.print_table(
                f"EvoCore Build Completed ({manifest.get('build_duration_seconds')}s)",
                [
                    ("Profile", profile),
                    ("Kernel SHA-256", f"{arts.get('vmlinuz_sha256')[:16]}..."),
                    ("InitRD SHA-256", f"{arts.get('initrd_sha256')[:16]}..."),
                    ("Rootfs Merkle", f"{arts.get('rootfs_merkle_root')[:16]}..."),
                    ("ISO Image", arts.get("iso_path")),
                    ("Output Dir", manifest.get("output_directory")),
                ],
            )
        formatter.emit_success(data, message="Appliance build succeeded.")

    except EvoCoreError as exc:
        formatter.emit_error(exc.message, exit_code=exc.exit_code, details=exc.details)
        ctx.exit(exc.exit_code)
    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_BUILD_FAILED)
        ctx.exit(EXIT_BUILD_FAILED)
