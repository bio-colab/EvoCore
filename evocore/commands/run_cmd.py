"""run_cmd.py — CLI command for booting and executing EvoCore experiments in QEMU."""
from __future__ import annotations

from pathlib import Path
import click

from evocore.constants import DEFAULT_PROFILE, EXIT_ERROR, EXIT_SUCCESS
from evocore.core.runner import EvoRunner
from evocore.utils.exceptions import EvoCoreError
from evocore.utils.output import common_cli_options, sync_output_formatter


@click.command("run", help="Boot EvoCore appliance in QEMU and execute scientific discovery.")
@click.option("--mode", "-m", type=click.Choice(["lab", "research", "iso"]), default="lab", help="Operating mode.")
@click.option("--profile", "-p", default=DEFAULT_PROFILE, help="Appliance profile (default: minimal).")
@click.option("--headless/--gui", default=True, help="Run headless or spawn visible GUI window.")
@click.option("--timeout", "-t", type=int, default=90, help="Execution timeout in seconds (default: 90).")
@click.option("--memory", type=int, default=512, help="VM RAM allocation in MB (default: 512).")
@click.option("--bundle/--no-bundle", default=False, help="Automatically pack results into sealed .evobundle.")
@click.option("--output-dir", "-o", type=click.Path(exists=False), default=None, help="Directory for logs and manifests.")
@common_cli_options
@click.pass_context
def run_cmd(
    ctx: click.Context,
    mode: str,
    profile: str,
    headless: bool,
    timeout: int,
    memory: int,
    bundle: bool,
    output_dir: str | None,
    json_mode: bool,
    quiet: bool,
    verbose: bool,
) -> None:
    formatter = sync_output_formatter(ctx, json_mode=json_mode, quiet=quiet, verbose=verbose)
    formatter.print_info(f"Launching EvoCore VM in {mode.upper()} mode (profile={profile}, headless={headless})...")

    try:
        runner = EvoRunner()
        result = runner.run(
            mode=mode,
            profile=profile,
            headless=headless,
            timeout=timeout,
            memory_mb=memory,
            create_bundle=bundle,
            output_dir=output_dir,
        )

        res_dict = result.to_dict()

        if not formatter.json_mode:
            if result.manifest:
                sol = result.manifest.get("solution", {})
                sigs = result.manifest.get("signatures", {})
                formatter.print_table(
                    f"EvoCore Discovery Telemetry ({result.duration_seconds}s)",
                    [
                        ("Discovered Formula", sol.get("expression", "N/A")),
                        ("Fitness Score", f"{sol.get('fitness_score', 0):.4f} / 100"),
                        ("Error Gap", f"{sol.get('e_gap', 0)*100:.3f}%"),
                        ("Physical Gates", "PASSED" if sol.get("passed_gates") else "FAILED"),
                        ("Specification SHA", f"{sigs.get('specification_sha256', '')[:16]}..."),
                        ("Solution Fingerprint", f"{sigs.get('solution_sha256', '')[:16]}..."),
                        ("Manifest Saved To", result.manifest_path),
                    ],
                )
                if result.bundle_path:
                    formatter.print_info(f"Sealed Evidence Capsule created: {result.bundle_path}")
            elif not headless:
                formatter.print_info("Interactive VM session spawned in background window.")
            else:
                formatter.print_info(f"Run completed in {result.duration_seconds}s. Log saved to {result.log_path}.")

        formatter.emit_success(res_dict, message="Execution finished successfully.")

    except EvoCoreError as exc:
        formatter.emit_error(exc.message, exit_code=exc.exit_code, details=exc.details)
        ctx.exit(exc.exit_code)
    except Exception as exc:
        formatter.emit_error(str(exc), exit_code=EXIT_ERROR)
        ctx.exit(EXIT_ERROR)
