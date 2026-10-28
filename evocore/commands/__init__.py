"""Command registrations for EvoCore."""
from evocore.commands.build_cmd import build_cmd
from evocore.commands.evidence_cmd import evidence_group
from evocore.commands.info_cmd import info_cmd
from evocore.commands.profile_cmd import profile_group
from evocore.commands.repl_cmd import repl_cmd
from evocore.commands.run_cmd import run_cmd

__all__ = [
    "build_cmd",
    "run_cmd",
    "evidence_group",
    "profile_group",
    "info_cmd",
    "repl_cmd",
]
