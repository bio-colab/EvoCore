"""test_profile.py — Tests for declarative appliance profile manager and validator."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from evocore.core.profile import ProfileManager
from evocore.utils.exceptions import EvoCoreArtifactNotFoundError, EvoCoreInvalidArgumentError


def test_list_builtin_profiles():
    pm = ProfileManager()
    profiles = pm.list_profiles()
    names = [p["name"] for p in profiles]
    assert "minimal" in names
    assert "symbolic" in names
    assert "eda" in names
    for p in profiles:
        assert p["valid"] is True


def test_load_profile_by_name():
    pm = ProfileManager()
    prof = pm.load_profile("minimal")
    assert prof["profile"] == "minimal"
    assert "experiment" in prof
    assert prof["experiment"]["domain"] == "stokes_newton_drag"


def test_load_nonexistent_profile():
    pm = ProfileManager()
    with pytest.raises(EvoCoreArtifactNotFoundError):
        pm.load_profile("non_existent_profile_xyz")


def test_validate_profile_schema():
    valid_data = {
        "name": "custom",
        "memory_mb": 256,
        "experiment": {"domain": "fluid_dynamics"},
    }
    is_valid, errors = ProfileManager.validate_profile(valid_data)
    assert is_valid is True
    assert len(errors) == 0

    invalid_data = {
        "memory_mb": 16,  # Less than 64
        "experiment": "not_a_dict",
    }
    is_valid, errors = ProfileManager.validate_profile(invalid_data)
    assert is_valid is False
    assert any("name" in e for e in errors)
    assert any("memory_mb" in e for e in errors)
    assert any("experiment" in e for e in errors)
