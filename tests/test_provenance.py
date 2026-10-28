"""test_provenance.py — Tests for deep cryptographic attestation and Merkle integrity."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from evocore.core.provenance import (
    calculate_merkle_root,
    compute_bytes_sha256,
    compute_composite_signature,
    compute_cpio_merkle,
    verify_evidence_manifest,
)
from evocore.core.forge import CpioEntry, write_cpio_archive


def test_merkle_root_determinism():
    """Verifies Merkle root computation produces deterministic root hashes regardless of input order."""
    hashes = [
        hashlib.sha256(b"file_1").hexdigest(),
        hashlib.sha256(b"file_2").hexdigest(),
        hashlib.sha256(b"file_3").hexdigest(),
        hashlib.sha256(b"file_4").hexdigest(),
    ]
    root1 = calculate_merkle_root(hashes)
    root2 = calculate_merkle_root(list(reversed(hashes)))
    assert root1 == root2
    assert len(root1) == 64


def test_merkle_root_odd_leaves():
    """Verifies Merkle root computation on odd number of leaf nodes."""
    hashes = [
        hashlib.sha256(b"alpha").hexdigest(),
        hashlib.sha256(b"beta").hexdigest(),
        hashlib.sha256(b"gamma").hexdigest(),
    ]
    root = calculate_merkle_root(hashes)
    assert len(root) == 64


def test_cpio_merkle_root():
    """Verifies in-memory CPIO archive Merkle root computation."""
    entries = [
        CpioEntry(name="etc/issue", mode=0o100644, data=b"EvoCore v0.3.0\n"),
        CpioEntry(name="bin/sh", mode=0o100755, data=b"#!/bin/sh\nexit 0\n"),
    ]
    archive_bytes = write_cpio_archive(entries)
    merkle_root, file_hashes = compute_cpio_merkle(archive_bytes)
    assert "etc/issue" in file_hashes
    assert "bin/sh" in file_hashes
    assert len(merkle_root) == 64


def test_verify_evidence_manifest_authentic():
    """Verifies that untampered manifest passes attestation checks."""
    spec = {"domain": "stokes_newton_drag", "seed": 42}
    solution = {"expression": "24 / Re", "fitness_score": 98.5}
    spec_sha = hashlib.sha256(json.dumps(spec, sort_keys=True).encode("utf-8")).hexdigest()
    sol_sha = hashlib.sha256(json.dumps(solution, sort_keys=True).encode("utf-8")).hexdigest()

    manifest = {
        "appliance": "EvoCore",
        "appliance_version": "0.3.0",
        "timestamp_utc": "2026-10-28 00:00:00",
        "signatures": {
            "specification_sha256": spec_sha,
            "solution_sha256": sol_sha,
        },
        "specification": spec,
        "solution": solution,
    }

    res = verify_evidence_manifest(manifest)
    assert res["valid"] is True
    assert len(res["tampered_fields"]) == 0


def test_verify_evidence_manifest_tampered():
    """Verifies that any modification to solution or spec is flagged as tampered."""
    spec = {"domain": "stokes_newton_drag", "seed": 42}
    solution = {"expression": "24 / Re", "fitness_score": 98.5}
    spec_sha = hashlib.sha256(json.dumps(spec, sort_keys=True).encode("utf-8")).hexdigest()
    sol_sha = hashlib.sha256(json.dumps(solution, sort_keys=True).encode("utf-8")).hexdigest()

    manifest = {
        "appliance": "EvoCore",
        "appliance_version": "0.3.0",
        "signatures": {
            "specification_sha256": spec_sha,
            "solution_sha256": sol_sha,
        },
        "specification": spec,
        "solution": solution,
    }

    # Tamper with the solution expression
    tampered_manifest = copy.deepcopy(manifest)
    tampered_manifest["solution"]["expression"] = "24 / (Re ** 2)"

    res = verify_evidence_manifest(tampered_manifest)
    assert res["valid"] is False
    assert "solution" in res["tampered_fields"]
