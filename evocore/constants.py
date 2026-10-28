"""constants.py — Central configuration, exit codes, and default paths for EvoCore."""
from __future__ import annotations

import sys
from pathlib import Path

VERSION = "0.3.0"
APPLIANCE_NAME = "EvoCore"
BANNER_TITLE = f"DARWIN-EVOLAB -- {APPLIANCE_NAME} v{VERSION} AUTONOMOUS SCIENTIFIC APPLIANCE"

# Deterministic Exit Codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_ARGS = 2
EXIT_QEMU_NOT_FOUND = 3
EXIT_ARTIFACT_NOT_FOUND = 4
EXIT_ATTESTATION_FAILED = 5
EXIT_TIMEOUT = 6
EXIT_BUILD_FAILED = 7

# Standard File and Directory Names
DEFAULT_BASE_ISO = "TinyCore-current.iso"
DEFAULT_PROFILE = "minimal"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_MANIFEST_NAME = "evidence_manifest.json"
DEFAULT_BUILD_MANIFEST = "build_manifest.json"
DEFAULT_BUNDLE_EXTENSION = ".evobundle"

# Upstream Tiny Core Base Image
UPSTREAM_ISO_URL = "http://tinycorelinux.net/17.x/x86/release/TinyCore-current.iso"

# SVR4 CPIO Archive Constants
CPIO_MAGIC = b"070701"
CPIO_BLOCK_SIZE = 512
ISO_SECTOR_SIZE = 2048

# Common Known QEMU Binary Locations
QEMU_CANDIDATE_PATHS = [
    r"C:\Program Files\qemu\qemu-system-x86_64.exe",
    r"C:\Program Files (x86)\qemu\qemu-system-x86_64.exe",
    r"C:\qemu\qemu-system-x86_64.exe",
    "/usr/bin/qemu-system-x86_64",
    "/usr/local/bin/qemu-system-x86_64",
    "/opt/homebrew/bin/qemu-system-x86_64",
]
