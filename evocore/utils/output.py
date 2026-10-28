"""output.py — Output formatting and contract rendering for EvoCore."""
from __future__ import annotations

import json
import sys
from typing import Any, Callable
import click


class OutputFormatter:
    """Manages CLI output rendering ensuring strict JSON machine contract or human TUI."""

    def __init__(self, json_mode: bool = False, quiet: bool = False, verbose: bool = False) -> None:
        self.json_mode = json_mode
        self.quiet = quiet
        self.verbose = verbose

    def emit_success(self, data: Any, message: str | None = None) -> None:
        """Emits successful command completion either as strict JSON or human-readable text."""
        if self.json_mode:
            payload = {
                "status": "success",
                "data": data,
            }
            if message:
                payload["message"] = message
            print(json.dumps(payload, indent=2, sort_keys=False))
        else:
            if message and not self.quiet:
                print(f"[OK] {message}")

    def emit_error(self, message: str, exit_code: int = 1, details: dict[str, Any] | None = None) -> None:
        """Emits an error either as strict JSON or formatted human-readable text."""
        if self.json_mode:
            payload = {
                "status": "error",
                "error": {
                    "code": exit_code,
                    "message": message,
                    "details": details or {},
                },
            }
            print(json.dumps(payload, indent=2, sort_keys=False))
        else:
            print(f"[!] Error: {message}", file=sys.stderr)
            if details and self.verbose:
                print(f"    Details: {json.dumps(details, indent=2)}", file=sys.stderr)

    def print_info(self, message: str) -> None:
        """Prints informational status message (suppressed in JSON or quiet mode)."""
        if not self.json_mode and not self.quiet:
            print(f"[*] {message}")

    def print_warning(self, message: str) -> None:
        """Prints warning message."""
        if not self.json_mode:
            print(f"[!] Warning: {message}", file=sys.stderr)

    def print_table(self, title: str, rows: list[tuple[str, Any]]) -> None:
        """Renders an aligned key-value summary table."""
        if self.json_mode or self.quiet:
            return
        print(f"\n=== {title} ===")
        max_k = max((len(k) for k, _ in rows), default=15)
        for k, v in rows:
            print(f"  {k.ljust(max_k)} : {v}")
        print("=" * (len(title) + 8))


def common_cli_options(f: Callable) -> Callable:
    """Decorator adding universal output flags (--json, --quiet, --verbose) to subcommands."""
    f = click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose diagnostics.")(f)
    f = click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress non-essential messages.")(f)
    f = click.option("--json", "json_mode", is_flag=True, default=False, help="Emit strict JSON output on stdout.")(f)
    return f


def sync_output_formatter(ctx: click.Context, json_mode: bool = False, quiet: bool = False, verbose: bool = False) -> OutputFormatter:
    """Ensures formatter state is updated whether flags are given to root or subcommand."""
    ctx.ensure_object(dict)
    formatter: OutputFormatter | None = ctx.obj.get("formatter")
    if formatter is None:
        formatter = OutputFormatter(json_mode=json_mode, quiet=quiet, verbose=verbose)
        ctx.obj["formatter"] = formatter
    else:
        if json_mode:
            formatter.json_mode = True
        if quiet:
            formatter.quiet = True
        if verbose:
            formatter.verbose = True
    return formatter
