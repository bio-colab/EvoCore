#!/usr/bin/env python3
"""test_evoforge.py — Automated verification test suite for EvoCore & EvoForge.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from evoforge import (
    CpioEntry,
    EvoForge,
    IsoInspector,
    read_cpio_archive,
    write_cpio_archive,
)
from supervisor.supervisor import (
    collect_hardware_telemetry,
    compute_environment_hash,
    execute_laboratory_experiment,
)


def test_cpio_archive_roundtrip():
    """Verifies SVR4 070701 CPIO archive generation, byte alignment, and parsing."""
    entries = [
        CpioEntry(name="etc/test.conf", mode=0o100644, data=b"evocore_test=true\n"),
        CpioEntry(name="bin/run", mode=0o100755, data=b"#!/bin/sh\necho hello\n"),
        CpioEntry(name="var/log", mode=0o040755, data=b""),
    ]
    raw_cpio = write_cpio_archive(entries)
    assert len(raw_cpio) % 512 == 0, "CPIO archive must be padded to 512-byte boundary"
    assert raw_cpio.startswith(b"070701"), "CPIO archive must start with SVR4 magic"

    parsed = read_cpio_archive(raw_cpio)
    names = [e.name for e in parsed]
    assert "etc/test.conf" in names
    assert "bin/run" in names
    assert "var/log" in names

    conf_entry = next(e for e in parsed if e.name == "etc/test.conf")
    assert conf_entry.data == b"evocore_test=true\n"
    assert conf_entry.mode == 0o100644

    run_entry = next(e for e in parsed if e.name == "bin/run")
    assert run_entry.data == b"#!/bin/sh\necho hello\n"
    assert run_entry.mode == 0o100755


def test_iso_inspector_base():
    """Verifies ISO9660 parsing on TinyCore-current.iso."""
    iso_path = Path(__file__).parent.parent / "TinyCore-current.iso"
    assert iso_path.exists(), "TinyCore-current.iso must exist in EvoCore/"

    inspector = IsoInspector(iso_path)
    assert inspector.volume_id == "TinyCore"
    assert "BOOT/CORE.GZ" in inspector.entries
    assert "BOOT/VMLINUZ" in inspector.entries

    core_bytes = inspector.get_file_bytes("BOOT/CORE.GZ")
    assert len(core_bytes) > 10_000_000
    assert core_bytes[:2] == b"\x1f\x8b", "CORE.GZ must have valid gzip magic"

    vmlinuz_bytes = inspector.get_file_bytes("BOOT/VMLINUZ")
    assert len(vmlinuz_bytes) > 5_000_000


def test_supervisor_telemetry_and_experiment(tmp_path):
    """Verifies hardware telemetry collection and evidence manifest generation."""
    telemetry = collect_hardware_telemetry()
    assert "system" in telemetry
    assert "python_version" in telemetry

    env_hash = compute_environment_hash(telemetry)
    assert len(env_hash) == 64

    spec = {
        "domain": "stokes_newton_drag",
        "level": "LC",
        "n_train": 20,
        "generations": 5,
        "population_size": 10,
        "seed": 42,
    }
    manifest = execute_laboratory_experiment(spec, tmp_path, telemetry)
    assert manifest["appliance"] == "EvoCore"
    assert manifest["contract"] == "REPRODUCIBLE_SCIENTIFIC_EVIDENCE"
    assert "signatures" in manifest
    assert len(manifest["signatures"]["solution_sha256"]) == 64

    manifest_file = tmp_path / "evidence_manifest.json"
    assert manifest_file.exists()


def test_evoforge_build_profile(tmp_path):
    """Verifies complete build pipeline for the minimal profile."""
    forge = EvoForge()
    manifest = forge.build_profile(
        profile_name="minimal",
        output_dir=tmp_path / "build_test",
    )

    assert manifest["appliance"] == "EvoCore"
    assert manifest["profile"] == "minimal"
    assert manifest["artifacts"]["iso_size"] > 0

    out_dir = tmp_path / "build_test"
    vmlinuz_path = out_dir / "boot" / "vmlinuz"
    core_path = out_dir / "boot" / "core.gz"
    iso_path = out_dir / "EvoCore-minimal.iso"
    build_manifest_path = out_dir / "build_manifest.json"

    assert vmlinuz_path.exists()
    assert core_path.exists()
    assert iso_path.exists()
    assert build_manifest_path.exists()

    # Verify that core.gz contains our injected EvoCore supervisor & overlay
    raw_initrd = gzip.decompress(core_path.read_bytes())
    entries = read_cpio_archive(raw_initrd)
    injected_names = [e.name for e in entries]

    assert "etc/os-release" in injected_names
    assert "opt/bootlocal.sh" in injected_names
    assert "opt/evocore/supervisor.py" in injected_names
    assert "opt/evocore/banner.txt" in injected_names
    assert "opt/evocore/experiment.json" in injected_names

    # Verify that the generated ISO can be inspected and contains valid files
    iso_inspector = IsoInspector(iso_path)
    iso_core = iso_inspector.get_file_bytes("BOOT/CORE.GZ")
    assert hashlib.sha256(iso_core).hexdigest() == manifest["artifacts"]["initrd_sha256"]


def test_svr4_device_nodes_in_remastered_initrd():
    """Verifies that device nodes preserve non-zero major and minor numbers for Linux kernel."""
    forge = EvoForge()
    iso_inspector = IsoInspector(forge.root / "TinyCore-current.iso")
    base_core = iso_inspector.get_file_bytes("BOOT/CORE.GZ")

    remastered = forge.remaster_initrd(
        base_core_gz=base_core,
        overlay_dir=forge.root / "overlay",
        supervisor_dir=forge.root / "supervisor",
        profile_data={"profile": "minimal"},
        embed_evolab=False,
    )
    raw = gzip.decompress(remastered)
    entries = read_cpio_archive(raw)
    dev_null = next((e for e in entries if e.name == "dev/null"), None)
    assert dev_null is not None
    assert dev_null.rmaj == 1
    assert dev_null.rmin == 3

    dev_console = next((e for e in entries if e.name == "dev/console"), None)
    assert dev_console is not None
    assert dev_console.rmaj == 5
    assert dev_console.rmin == 1


def test_extract_manifest_helper(tmp_path):
    """Verifies extract_manifest helper parsing."""
    from extract_manifest import extract

    sample_log = """
    Random boot log noise...
    === BEGIN EVOCORE EVIDENCE MANIFEST ===
    {
      "appliance": "EvoCore",
      "version": "0.2.0",
      "signatures": {
        "solution_sha256": "abcdef1234567890"
      }
    }
    === END EVOCORE EVIDENCE MANIFEST ===
    Power down complete.
    """
    log_file = tmp_path / "serial.log"
    out_file = tmp_path / "extracted.json"
    log_file.write_text(sample_log, encoding="utf-8")

    assert extract(log_file, out_file) is True
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["appliance"] == "EvoCore"
    assert data["version"] == "0.2.0"

