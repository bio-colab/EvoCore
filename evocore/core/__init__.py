"""Core engine modules for EvoCore."""
from evocore.core.bundle import EvidenceBundle
from evocore.core.forge import CpioEntry, EvoForge, IsoInspector, read_cpio_archive, write_cpio_archive
from evocore.core.profile import ProfileManager
from evocore.core.provenance import (
    calculate_merkle_root,
    compute_cpio_merkle,
    compute_directory_merkle,
    compute_composite_signature,
    verify_evidence_manifest,
)
from evocore.core.runner import EvoRunner, RunResult, extract_manifest_from_log

__all__ = [
    "CpioEntry",
    "read_cpio_archive",
    "write_cpio_archive",
    "IsoInspector",
    "EvoForge",
    "ProfileManager",
    "EvidenceBundle",
    "calculate_merkle_root",
    "compute_cpio_merkle",
    "compute_directory_merkle",
    "compute_composite_signature",
    "verify_evidence_manifest",
    "EvoRunner",
    "RunResult",
    "extract_manifest_from_log",
]
