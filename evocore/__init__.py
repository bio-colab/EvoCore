"""EvoCore — Autonomous Scientific Appliance & Experimental Operating System.

Sovereign package for appliance remastering, sandboxed scientific discovery,
and cryptographic evidence attestation.
"""
from evocore.constants import VERSION
from evocore.core.bundle import EvidenceBundle
from evocore.core.forge import CpioEntry, EvoForge, IsoInspector
from evocore.core.profile import ProfileManager
from evocore.core.provenance import (
    calculate_merkle_root,
    compute_composite_signature,
    compute_cpio_merkle,
    compute_directory_merkle,
    verify_evidence_manifest,
)
from evocore.core.runner import EvoRunner, RunResult

__version__ = VERSION

__all__ = [
    "__version__",
    "EvoForge",
    "EvoRunner",
    "EvidenceBundle",
    "ProfileManager",
    "IsoInspector",
    "CpioEntry",
    "RunResult",
    "calculate_merkle_root",
    "compute_composite_signature",
    "compute_cpio_merkle",
    "compute_directory_merkle",
    "verify_evidence_manifest",
]
