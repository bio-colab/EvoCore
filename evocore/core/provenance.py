"""provenance.py — Deep cryptographic attestation and Merkle integrity verification for EvoCore."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from evocore.constants import CPIO_MAGIC


def compute_file_sha256(path: Path | str) -> str:
    """Computes SHA-256 digest of a local file in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Computes SHA-256 digest of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def calculate_merkle_root(leaf_hashes: list[str]) -> str:
    """Computes standard deterministic Merkle root hash from a list of leaf SHA-256 digests."""
    if not leaf_hashes:
        return hashlib.sha256(b"").hexdigest()

    current_level = sorted(leaf_hashes)

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = hashlib.sha256(f"{left}:{right}".encode("ascii")).hexdigest()
            next_level.append(combined)
        current_level = next_level

    return current_level[0]


def compute_directory_merkle(directory: Path | str) -> tuple[str, dict[str, str]]:
    """Walks directory, calculates SHA-256 for each file, and computes root Merkle hash."""
    base_dir = Path(directory)
    if not base_dir.is_dir():
        return hashlib.sha256(b"").hexdigest(), {}

    file_hashes: dict[str, str] = {}
    for p in sorted(base_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(base_dir).as_posix()
            file_hashes[rel] = compute_file_sha256(p)

    leaves = [f"{rel}:{h}" for rel, h in file_hashes.items()]
    merkle_root = calculate_merkle_root(leaves)
    return merkle_root, file_hashes


def compute_cpio_merkle(raw_cpio_or_gz: bytes) -> tuple[str, dict[str, str]]:
    """Computes Merkle root of files within a CPIO or gzipped CPIO archive without writing to disk."""
    data = raw_cpio_or_gz
    # Decompress if gzipped
    if data[:2] == b"\x1f\x8b":
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            data = gz.read()

    pos = 0
    n = len(data)
    file_hashes: dict[str, str] = {}

    while pos + 110 <= n:
        magic = data[pos : pos + 6]
        if magic != CPIO_MAGIC:
            break

        header = data[pos : pos + 110]
        mode = int(header[14:22], 16)
        filesize = int(header[54:62], 16)
        namesize = int(header[94:102], 16)

        name_offset = pos + 110
        name = data[name_offset : name_offset + namesize - 1].decode("latin1", errors="replace")
        if name == "TRAILER!!!":
            break

        head_name_len = 110 + namesize
        head_pad = (4 - (head_name_len % 4)) % 4
        file_start = pos + head_name_len + head_pad
        file_data = data[file_start : file_start + filesize]
        file_pad = (4 - (filesize % 4)) % 4

        is_dir = (mode & 0o170000) == 0o040000
        if not is_dir and filesize > 0:
            file_hashes[name] = compute_bytes_sha256(file_data)

        pos = file_start + filesize + file_pad

    leaves = [f"{rel}:{h}" for rel, h in file_hashes.items()]
    merkle_root = calculate_merkle_root(leaves)
    return merkle_root, file_hashes


def compute_composite_signature(
    kernel_sha256: str,
    initrd_sha256: str,
    rootfs_merkle: str,
    spec_sha256: str,
    solution_sha256: str,
) -> str:
    """Calculates canonical composite cryptographic signature combining all physical and mathematical layers."""
    vector = f"{kernel_sha256}|{initrd_sha256}|{rootfs_merkle}|{spec_sha256}|{solution_sha256}"
    return hashlib.sha256(vector.encode("utf-8")).hexdigest()


def verify_evidence_manifest(
    manifest_data: dict[str, Any],
    kernel_path: Path | str | None = None,
    initrd_path: Path | str | None = None,
) -> dict[str, Any]:
    """Forensically audits an evidence manifest, checking spec, solution, and artifact hashes."""
    checks: dict[str, Any] = {}
    tampered_fields: list[str] = []

    sigs = manifest_data.get("signatures", {})
    spec = manifest_data.get("specification", {})
    solution = manifest_data.get("solution", {})

    # 1. Verify Specification Hash
    expected_spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode("utf-8")).hexdigest()
    spec_valid = (sigs.get("specification_sha256") == expected_spec_hash)
    checks["specification_integrity"] = {
        "valid": spec_valid,
        "recorded": sigs.get("specification_sha256"),
        "computed": expected_spec_hash,
    }
    if not spec_valid:
        tampered_fields.append("specification")

    # 2. Verify Solution Hash
    expected_sol_hash = hashlib.sha256(json.dumps(solution, sort_keys=True).encode("utf-8")).hexdigest()
    sol_valid = (sigs.get("solution_sha256") == expected_sol_hash)
    checks["solution_integrity"] = {
        "valid": sol_valid,
        "recorded": sigs.get("solution_sha256"),
        "computed": expected_sol_hash,
    }
    if not sol_valid:
        tampered_fields.append("solution")

    # 3. Verify Kernel if provided
    if kernel_path and Path(kernel_path).is_file():
        actual_k_hash = compute_file_sha256(kernel_path)
        expected_k_hash = sigs.get("kernel_sha256")
        k_valid = (expected_k_hash is None or expected_k_hash == actual_k_hash)
        checks["kernel_binary_integrity"] = {
            "valid": k_valid,
            "recorded": expected_k_hash,
            "computed": actual_k_hash,
        }
        if not k_valid:
            tampered_fields.append("kernel_binary")

    # 4. Verify Initrd if provided
    if initrd_path and Path(initrd_path).is_file():
        actual_initrd_hash = compute_file_sha256(initrd_path)
        expected_initrd_hash = sigs.get("initrd_sha256")
        initrd_valid = (expected_initrd_hash is None or expected_initrd_hash == actual_initrd_hash)
        checks["initrd_binary_integrity"] = {
            "valid": initrd_valid,
            "recorded": expected_initrd_hash,
            "computed": actual_initrd_hash,
        }
        if not initrd_valid:
            tampered_fields.append("initrd_binary")

    # 5. Verify Composite Signature if present
    recorded_comp = sigs.get("composite_signature")
    if recorded_comp:
        recalc_comp = compute_composite_signature(
            kernel_sha256=sigs.get("kernel_sha256", ""),
            initrd_sha256=sigs.get("initrd_sha256", ""),
            rootfs_merkle=sigs.get("rootfs_merkle_root", ""),
            spec_sha256=expected_spec_hash,
            solution_sha256=expected_sol_hash,
        )
        comp_valid = (recorded_comp == recalc_comp)
        checks["composite_signature"] = {
            "valid": comp_valid,
            "recorded": recorded_comp,
            "computed": recalc_comp,
        }
        if not comp_valid:
            tampered_fields.append("composite_signature")

    overall_valid = len(tampered_fields) == 0

    return {
        "valid": overall_valid,
        "appliance": manifest_data.get("appliance", "EvoCore"),
        "version": manifest_data.get("appliance_version", "unknown"),
        "timestamp_utc": manifest_data.get("timestamp_utc"),
        "tampered_fields": tampered_fields,
        "checks": checks,
    }
