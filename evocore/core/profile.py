"""profile.py — Declarative appliance profile manager and validator for EvoCore."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evocore.utils.exceptions import EvoCoreArtifactNotFoundError, EvoCoreInvalidArgumentError


class ProfileManager:
    """Discovers, validates, and resolves declarative appliance build profiles."""

    def __init__(self, profiles_dir: Path | str | None = None) -> None:
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            self.profiles_dir = Path(__file__).resolve().parent.parent.parent / "profiles"

    def list_profiles(self) -> list[dict[str, Any]]:
        """Lists all available appliance profiles with metadata."""
        if not self.profiles_dir.is_dir():
            return []

        results = []
        for p in sorted(self.profiles_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                valid, errors = self.validate_profile(data)
                results.append({
                    "name": data.get("name") or data.get("profile") or p.stem,
                    "file_stem": p.stem,
                    "path": str(p),
                    "description": data.get("description", "No description provided"),
                    "memory_mb": data.get("memory_mb", 512),
                    "mode": data.get("default_mode") or data.get("mode", "lab"),
                    "domain": data.get("experiment", {}).get("domain", "N/A"),
                    "valid": valid,
                    "validation_errors": errors,
                })
            except Exception as exc:
                results.append({
                    "name": p.stem,
                    "file_stem": p.stem,
                    "path": str(p),
                    "valid": False,
                    "validation_errors": [str(exc)],
                })
        return results

    def load_profile(self, name_or_path: str) -> dict[str, Any]:
        """Loads and parses a profile configuration by name or direct file path."""
        candidate = Path(name_or_path)
        if not candidate.is_file():
            candidate = self.profiles_dir / f"{name_or_path}.json"

        if not candidate.is_file():
            available = [p["name"] for p in self.list_profiles()]
            raise EvoCoreArtifactNotFoundError(
                f"Profile '{name_or_path}' not found. Available profiles: {available}"
            )

        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise EvoCoreInvalidArgumentError(f"Profile JSON decode error in {candidate}: {exc}")

        valid, errors = self.validate_profile(data)
        if not valid:
            raise EvoCoreInvalidArgumentError(
                f"Invalid profile configuration in {candidate}: {', '.join(errors)}"
            )

        data["_profile_name"] = candidate.stem
        data["_profile_path"] = str(candidate)
        return data

    @staticmethod
    def validate_profile(data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validates a profile structure against EvoCore appliance schema."""
        errors: list[str] = []
        if not isinstance(data, dict):
            return False, ["Profile must be a JSON object"]

        if "name" not in data and "profile" not in data:
            errors.append("Missing required field: 'name' or 'profile'")

        mem = data.get("memory_mb")
        if mem is not None:
            if not isinstance(mem, int) or mem < 64:
                errors.append("'memory_mb' must be an integer >= 64")

        exp = data.get("experiment")
        if exp is not None:
            if not isinstance(exp, dict):
                errors.append("'experiment' must be an object")
            elif "domain" not in exp:
                errors.append("'experiment' must declare 'domain'")

        return len(errors) == 0, errors
