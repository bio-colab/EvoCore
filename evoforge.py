#!/usr/bin/env python3
"""evoforge.py — The Autonomous Build & Remastering Engine for EvoCore.

Maintains full backward compatibility with EvoCore v0.2 while delegating to
the modern evocore.core.forge engine.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from evocore.constants import VERSION as EVOCORE_VERSION
from evocore.core.forge import (
    CpioEntry,
    EvoForge,
    IsoInspector,
    read_cpio_archive,
    write_cpio_archive,
)

EVOFORGE_VERSION = EVOCORE_VERSION
CPIO_MAGIC = b"070701"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EvoForge — EvoCore Appliance Generator")
    sub = parser.add_subparsers(dest="command", required=True)

    # Subcommand: inspect
    p_insp = sub.add_parser("inspect", help="Inspect an existing Tiny Core or EvoCore ISO")
    p_insp.add_argument("iso", type=str, help="Path to ISO image")

    # Subcommand: build
    p_bld = sub.add_parser("build", help="Build remastered EvoCore boot bundle from profile")
    p_bld.add_argument("--profile", default="minimal", choices=["minimal", "symbolic", "eda"], help="Profile name")
    p_bld.add_argument("--base", default=None, help="Base ISO image (defaults to TinyCore-current.iso)")
    p_bld.add_argument("--output-dir", default=None, help="Output destination")

    # Subcommand: test-supervisor
    p_sup = sub.add_parser("test-supervisor", help="Executes the supervisor in-process for testing")
    p_sup.add_argument("--mode", default="lab", choices=["lab", "research"])

    args = parser.parse_args(argv)
    forge = EvoForge()

    if args.command == "inspect":
        res = forge.inspect(args.iso)
        print(f"=== EvoForge Inspection Report for {args.iso} ===")
        print(f"  Volume ID        : {res['volume_id']}")
        print(f"  ISO Size (MB)    : {res['file_size_mb']}")
        print(f"  ISO SHA-256      : {res['sha256']}")
        print(f"  Kernel Detected  : {res['kernel_detected']['name'] if res['kernel_detected'] else 'None'}")
        print(f"  InitRD Detected  : {res['initrd_detected']['name'] if res['initrd_detected'] else 'None'}")
        print(f"  Total Files      : {res['total_files']}")

    elif args.command == "build":
        print(f"[EvoForge] Building EvoCore appliance for profile: {args.profile}...")
        manifest = forge.build_profile(profile_name=args.profile, base_iso=args.base, output_dir=args.output_dir)
        print(f"[EvoForge] Build completed successfully in {manifest['build_duration_seconds']}s!")
        print(f"           Kernel SHA-256 : {manifest['artifacts']['vmlinuz_sha256'][:16]}...")
        print(f"           InitRD SHA-256 : {manifest['artifacts']['initrd_sha256'][:16]}... ({manifest['artifacts']['initrd_size']} bytes)")
        print(f"           Output Root    : {manifest['output_directory']}")
        print(f"           Manifest File  : {Path(manifest['output_directory']) / 'build_manifest.json'}")

    elif args.command == "test-supervisor":
        from supervisor.supervisor import main as sup_main
        return sup_main(["--mode", args.mode, "--output-dir", "EvoCore/output/test_run"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
