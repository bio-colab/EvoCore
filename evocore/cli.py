"""cli.py — Master Click entry point and command router for EvoCore."""
from __future__ import annotations

import sys
import click

from evocore.constants import BANNER_TITLE, VERSION
from evocore.commands import (
    build_cmd,
    evidence_group,
    info_cmd,
    profile_group,
    repl_cmd,
    run_cmd,
)
from evocore.utils.output import OutputFormatter


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--json", "json_mode", is_flag=True, default=False, help="Emit strict JSON output on stdout.")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress non-essential messages.")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose diagnostics.")
@click.version_option(version=VERSION, prog_name="evocore")
@click.pass_context
def main(ctx: click.Context, json_mode: bool, quiet: bool, verbose: bool) -> None:
    """EvoCore — The Sovereign Autonomous Scientific Appliance & Operating System.

    Provides a stateful CLI harness for pure-Python appliance remastering,
    sandboxed QEMU execution, and forensic cryptographic evidence attestation.
    """
    ctx.ensure_object(dict)
    formatter = OutputFormatter(json_mode=json_mode, quiet=quiet, verbose=verbose)
    ctx.obj["formatter"] = formatter
    ctx.obj["json"] = json_mode
    ctx.obj["quiet"] = quiet
    ctx.obj["verbose"] = verbose

    # If invoked with no subcommand:
    if ctx.invoked_subcommand is None:
        # If in interactive TTY and not in json mode, launch REPL
        if sys.stdin.isatty() and sys.stdout.isatty() and not json_mode:
            ctx.invoke(repl_cmd)
        else:
            click.echo(ctx.get_help())


# Register commands
main.add_command(build_cmd)
main.add_command(run_cmd)
main.add_command(evidence_group)
main.add_command(profile_group)
main.add_command(info_cmd)
main.add_command(repl_cmd)


if __name__ == "__main__":
    main()
