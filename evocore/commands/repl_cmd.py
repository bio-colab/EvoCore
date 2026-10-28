"""repl_cmd.py — Interactive REPL shell with autocomplete, history, and session state."""
from __future__ import annotations

import shlex
import sys
import click

from evocore.constants import BANNER_TITLE, VERSION


@click.command("repl", help="Start an interactive EvoCore session shell.")
@click.pass_context
def repl_cmd(ctx: click.Context) -> None:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.styles import Style
    except ImportError:
        click.echo("[!] prompt_toolkit is required for interactive REPL. Install with 'pip install prompt_toolkit'.")
        return

    commands = [
        "build",
        "run",
        "run --mode lab",
        "run --mode research",
        "run --mode iso",
        "run --gui",
        "run --bundle",
        "evidence",
        "evidence verify",
        "evidence inspect",
        "evidence bundle",
        "evidence unpack",
        "profile",
        "profile list",
        "profile show minimal",
        "profile validate",
        "info",
        "help",
        "clear",
        "exit",
        "quit",
    ]

    completer = WordCompleter(commands, ignore_case=True, sentence=True)
    history = InMemoryHistory()
    session = PromptSession(completer=completer, history=history)

    click.echo("=" * 75)
    click.echo(f"  {BANNER_TITLE}")
    click.echo("  Interactive REPL Shell. Type 'help' for commands, 'exit' to quit.")
    click.echo("=" * 75)

    root_cli = ctx.find_root().command

    while True:
        try:
            user_input = session.prompt("evocore> ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                click.echo("Terminating EvoCore session. Goodbye.")
                break

            if user_input.lower() == "clear":
                click.clear()
                continue

            if user_input.lower() == "help":
                with click.Context(root_cli) as help_ctx:
                    click.echo(root_cli.get_help(help_ctx))
                continue

            # Tokenize and execute through Click
            args = shlex.split(user_input)
            try:
                root_cli.main(args=args, standalone_mode=False)
            except click.ClickException as e:
                e.show()
            except SystemExit:
                pass
            except Exception as exc:
                click.echo(f"[!] Error: {exc}", err=True)

        except (KeyboardInterrupt, EOFError):
            click.echo("\nSession terminated.")
            break
