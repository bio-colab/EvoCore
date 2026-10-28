"""exceptions.py — Deterministic typed exceptions for EvoCore."""
from __future__ import annotations

from typing import Any
from evocore.constants import (
    EXIT_ERROR,
    EXIT_INVALID_ARGS,
    EXIT_QEMU_NOT_FOUND,
    EXIT_ARTIFACT_NOT_FOUND,
    EXIT_ATTESTATION_FAILED,
    EXIT_TIMEOUT,
    EXIT_BUILD_FAILED,
)


class EvoCoreError(Exception):
    """Base exception for all EvoCore operational errors."""
    exit_code: int = EXIT_ERROR

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "exit_code": self.exit_code,
            "details": self.details,
        }


class EvoCoreInvalidArgumentError(EvoCoreError):
    exit_code = EXIT_INVALID_ARGS


class EvoCoreQemuNotFoundError(EvoCoreError):
    exit_code = EXIT_QEMU_NOT_FOUND


class EvoCoreArtifactNotFoundError(EvoCoreError):
    exit_code = EXIT_ARTIFACT_NOT_FOUND


class EvoCoreAttestationError(EvoCoreError):
    exit_code = EXIT_ATTESTATION_FAILED


class EvoCoreTimeoutError(EvoCoreError):
    exit_code = EXIT_TIMEOUT


class EvoCoreBuildError(EvoCoreError):
    exit_code = EXIT_BUILD_FAILED
