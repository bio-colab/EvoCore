"""bundle.py — Sealed evidence capsule (.evobundle) packaging, extraction, and verification."""
from __future__ import annotations

import io
import json
import tarfile
import time
from pathlib import Path
from typing import Any

from evocore.constants import DEFAULT_BUNDLE_EXTENSION
from evocore.core.provenance import (
    calculate_merkle_root,
    compute_bytes_sha256,
    verify_evidence_manifest,
)
from evocore.utils.exceptions import EvoCoreArtifactNotFoundError, EvoCoreAttestationError


class EvidenceBundle:
    """Manages creation, verification, and inspection of sealed .evobundle archives."""

    @staticmethod
    def pack(
        manifest_data: dict[str, Any],
        output_path: Path | str,
        log_text: str | None = None,
        extra_files: dict[str, bytes] | None = None,
    ) -> Path:
        """Packs evidence manifest, logs, and cryptographic proofs into a sealed .evobundle."""
        out_p = Path(output_path)
        if not out_p.name.endswith(DEFAULT_BUNDLE_EXTENSION):
            out_p = out_p.with_suffix(DEFAULT_BUNDLE_EXTENSION)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            # 1. Manifest
            m_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")
            m_info = tarfile.TarInfo(name="evidence_manifest.json")
            m_info.size = len(m_bytes)
            m_info.mtime = int(time.time())
            tar.addfile(m_info, io.BytesIO(m_bytes))

            # 2. Raw Log if provided
            if log_text:
                l_bytes = log_text.encode("utf-8", errors="replace")
                l_info = tarfile.TarInfo(name="execution.log")
                l_info.size = len(l_bytes)
                l_info.mtime = int(time.time())
                tar.addfile(l_info, io.BytesIO(l_bytes))

            # 3. Extra attachments
            if extra_files:
                for fname, fbytes in extra_files.items():
                    e_info = tarfile.TarInfo(name=f"attachments/{fname}")
                    e_info.size = len(fbytes)
                    e_info.mtime = int(time.time())
                    tar.addfile(e_info, io.BytesIO(fbytes))

        out_p.write_bytes(buf.getvalue())
        return out_p

    @staticmethod
    def inspect(bundle_path: Path | str) -> dict[str, Any]:
        """Inspects .evobundle archive contents without extracting to disk."""
        b_path = Path(bundle_path)
        if not b_path.is_file():
            raise EvoCoreArtifactNotFoundError(f"Bundle file not found: {b_path}")

        entries: list[dict[str, Any]] = []
        manifest_data: dict[str, Any] | None = None

        with tarfile.open(b_path, mode="r:gz") as tar:
            for member in tar.getmembers():
                entries.append({
                    "name": member.name,
                    "size_bytes": member.size,
                    "is_file": member.isfile(),
                    "mtime": member.mtime,
                })
                if member.name == "evidence_manifest.json":
                    f = tar.extractfile(member)
                    if f:
                        manifest_data = json.loads(f.read().decode("utf-8"))

        return {
            "bundle_path": str(b_path),
            "bundle_size_bytes": b_path.stat().st_size,
            "total_entries": len(entries),
            "entries": entries,
            "manifest": manifest_data,
        }

    @staticmethod
    def verify(bundle_path: Path | str) -> dict[str, Any]:
        """Verifies the internal cryptographic integrity of an .evobundle."""
        info = EvidenceBundle.inspect(bundle_path)
        manifest = info.get("manifest")
        if not manifest:
            raise EvoCoreAttestationError("Bundle is missing 'evidence_manifest.json'")

        verification = verify_evidence_manifest(manifest)
        verification["bundle_path"] = str(bundle_path)
        verification["bundle_size_bytes"] = info["bundle_size_bytes"]
        return verification

    @staticmethod
    def unpack(bundle_path: Path | str, destination_dir: Path | str) -> list[str]:
        """Unpacks .evobundle to target directory."""
        b_path = Path(bundle_path)
        dest = Path(destination_dir)
        dest.mkdir(parents=True, exist_ok=True)

        extracted_files: list[str] = []
        with tarfile.open(b_path, mode="r:gz") as tar:
            if hasattr(tarfile, "data_filter"):
                tar.extractall(path=dest, filter="data")
            else:
                tar.extractall(path=dest)
            for m in tar.getmembers():
                extracted_files.append((dest / m.name).as_posix())

        return extracted_files
