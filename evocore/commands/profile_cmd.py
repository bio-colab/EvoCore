"""profile_cmd.py — CLI commands for listing, inspecting, and validating appliance profiles."""
from __future__ import annotations

import json
from pathlib import Path
import click

from evocore.constants import EXIT_ERROR, EXIT_INVALID_ARGS, EXIT_SUCCESS
from evocore.core.profile import ProfileManager
from evocore.utils.exceptions import EvoCoreError
from evocore.utils.output import common_cli_options, sync_output_formatter


@click.group("profile", help="Manage, inspect, and validate declarative appliance profiles.")
def profile_group() -> None:
    pass


@profile_group.command("list", help="List all available EvoCore profiles.")
@common_cli_options
@click.pass_context
def list_profiles_cmd(ctx: click.Context, json_mode: bool, quiet: bool, verbose: bool) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    pm = ProfileManager()
    profiles = pm.list_profiles()

    if not formatter.json_mode:
        rows = [(p["name"], f"{p['description']} (RAM: {p['memory_mb']}MB, Valid: {p['valid']})") for p in profiles]
        formatter.print_table("Available Appliance Profiles", rows)

    formatter.emit_success(profiles)


@profile_group.command("show", help="Display full declarative JSON specification for a profile.")
@click.argument("name")
@common_cli_options
@click.pass_context
def show_profile_cmd(ctx: click.Context, name: str, json_mode: bool, quiet: bool, verbose: bool) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    pm = ProfileManager()

    try:
        prof = pm.load_profile(name)
        if not formatter.json_mode:
            formatter.print_table(
                f"Profile: {name}",
                [
                    ("Description", prof.get("description")),
                    ("Memory MB", prof.get("memory_mb")),
                    ("Default Mode", prof.get("default_mode", prof.get("mode"))),
                    ("Domain", prof.get("experiment", {}).get("domain")),
                    ("Path", prof.get("_profile_path")),
                ],
            )
        formatter.emit_success(prof)
    except EvoCoreError as exc:
        formatter.emit_error(exc.message, exit_code=exc.exit_code, details=exc.details)
        ctx.exit(exc.exit_code)
    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)


@profile_group.command("validate", help="Validate a custom profile JSON against EvoCore schema.")
@click.argument("path", type=click.Path(exists=True))
@common_cli_options
@click.pass_context
def validate_profile_cmd(ctx: click.Context, path: str, json_mode: bool, quiet: bool, verbose: bool) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    pm = ProfileManager()

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        valid, errors = pm.validate_profile(data)

        res = {
            "path": path,
            "valid": valid,
            "errors": errors,
        }

        if valid:
            formatter.emit_success(res, message=f"Profile at {path} is valid.")
        else:
            formatter.emit_error(
                f"Profile validation failed: {', '.join(errors)}",
                exit_code=EXIT_INVALID_ARGS,
                details=res,
            )
            ctx.exit(EXIT_INVALID_ARGS)
    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)
