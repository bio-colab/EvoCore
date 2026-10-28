"""test_bundle.py — Tests for .evobundle capsule packaging, integrity, and extraction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from evocore.core.bundle import EvidenceBundle
from evocore.utils.exceptions import EvoCoreArtifactNotFoundError


@pytest.fixture
def sample_manifest() -> dict:
    spec = {"domain": "stokes_newton_drag", "seed": 101}
    sol = {"expression": "24 / Re + 0.44", "fitness_score": 99.2, "passed_gates": True}
    return {
        "appliance": "EvoCore",
        "appliance_version": "0.3.0",
        "timestamp_utc": "2026-10-28 12:00:00",
        "signatures": {
            "specification_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True).encode("utf-8")).hexdigest(),
            "solution_sha256": hashlib.sha256(json.dumps(sol, sort_keys=True).encode("utf-8")).hexdigest(),
        },
        "specification": spec,
        "solution": sol,
    }


def test_bundle_pack_inspect_and_verify(tmp_path: Path, sample_manifest: dict):
    bundle_file = tmp_path / "test_run.evobundle"
    log_content = "Booting EvoCore VM...\nEvolution complete.\n"

    # Pack
    out_path = EvidenceBundle.pack(
        manifest_data=sample_manifest,
        output_path=bundle_file,
        log_text=log_content,
    )
    assert out_path.is_file()

    # Inspect
    info = EvidenceBundle.inspect(out_path)
    assert info["bundle_size_bytes"] > 0
    assert info["total_entries"] == 2
    assert info["manifest"]["appliance"] == "EvoCore"

    # Verify
    verification = EvidenceBundle.verify(out_path)
    assert verification["valid"] is True
    assert len(verification["tampered_fields"]) == 0

    # Unpack
    extract_dir = tmp_path / "extracted"
    files = EvidenceBundle.unpack(out_path, extract_dir)
    assert len(files) == 2
    assert (extract_dir / "evidence_manifest.json").is_file()
    assert (extract_dir / "execution.log").is_file()


def test_bundle_not_found(tmp_path: Path):
    with pytest.raises(EvoCoreArtifactNotFoundError):
        EvidenceBundle.inspect(tmp_path / "missing.evobundle")
