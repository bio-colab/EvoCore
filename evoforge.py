#!/usr/bin/env python3
"""evoforge.py — The Autonomous Build & Remastering Engine for EvoCore.

Enables pure-Python inspection, CPIO initramfs injection, profile compilation,
and bootloader configuration for Darwin-Evolab Experimental Linux (EvoCore).
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import gzip
import hashlib
import io
import json
import os
import shutil
import struct
import sys
import time
from pathlib import Path
from typing import Any

EVOFORGE_VERSION = "0.2.0"
EVOCORE_VERSION = "0.2.0"
CPIO_MAGIC = b"070701"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclasses.dataclass
class CpioEntry:
    """A single file, directory, device node, or link entry in a SVR4 '070701' CPIO archive."""
    name: str
    mode: int
    uid: int = 0
    gid: int = 0
    nlink: int = 1
    mtime: int = int(time.time())
    maj: int = 3
    min_: int = 1
    rmaj: int = 0
    rmin: int = 0
    ino: int = 0
    data: bytes = b""

    @property
    def is_dir(self) -> bool:
        return (self.mode & 0o170000) == 0o040000

    @property
    def is_char_dev(self) -> bool:
        return (self.mode & 0o170000) == 0o020000

    @property
    def is_block_dev(self) -> bool:
        return (self.mode & 0o170000) == 0o060000


def read_cpio_archive(raw_bytes: bytes) -> list[CpioEntry]:
    """Parses SVR4 '070701' new ASCII format CPIO archive."""
    entries: list[CpioEntry] = []
    pos = 0
    n = len(raw_bytes)

    while pos + 110 <= n:
        magic = raw_bytes[pos : pos + 6]
        if magic != CPIO_MAGIC:
            break

        header = raw_bytes[pos : pos + 110]
        ino = int(header[6:14], 16)
        mode = int(header[14:22], 16)
        uid = int(header[22:30], 16)
        gid = int(header[30:38], 16)
        nlink = int(header[38:46], 16)
        mtime = int(header[46:54], 16)
        filesize = int(header[54:62], 16)
        maj = int(header[62:70], 16)
        min_ = int(header[70:78], 16)
        rmaj = int(header[78:86], 16)
        rmin = int(header[86:94], 16)
        namesize = int(header[94:102], 16)

        name_offset = pos + 110
        name = raw_bytes[name_offset : name_offset + namesize - 1].decode("latin1")
        if name == "TRAILER!!!":
            break

        head_name_len = 110 + namesize
        head_pad = (4 - (head_name_len % 4)) % 4
        file_start = pos + head_name_len + head_pad
        file_data = raw_bytes[file_start : file_start + filesize]
        file_pad = (4 - (filesize % 4)) % 4

        entries.append(
            CpioEntry(
                name=name,
                mode=mode,
                uid=uid,
                gid=gid,
                nlink=nlink,
                mtime=mtime,
                maj=maj,
                min_=min_,
                rmaj=rmaj,
                rmin=rmin,
                ino=ino,
                data=file_data,
            )
        )
        pos = file_start + filesize + file_pad

    return entries


def write_cpio_archive(entries: list[CpioEntry]) -> bytes:
    """Serializes CpioEntry list into standard SVR4 '070701' CPIO archive with 512-byte padding."""
    out = io.BytesIO()

    for idx, e in enumerate(entries, start=1):
        name_bytes = e.name.encode("latin1") + b"\x00"
        namesize = len(name_bytes)
        filesize = len(e.data)
        ino = e.ino if e.ino != 0 else idx

        # Build 110-byte header
        # c_magic (6), c_ino (8), c_mode (8), c_uid (8), c_gid (8), c_nlink (8),
        # c_mtime (8), c_filesize (8), c_maj (8), c_min (8), c_rmaj (8), c_rmin (8),
        # c_namesize (8), c_check (8)
        header_str = (
            f"070701"
            f"{ino:08X}"
            f"{e.mode:08X}"
            f"{e.uid:08X}"
            f"{e.gid:08X}"
            f"{e.nlink:08X}"
            f"{e.mtime:08X}"
            f"{filesize:08X}"
            f"{e.maj:08X}"
            f"{e.min_:08X}"
            f"{e.rmaj:08X}"
            f"{e.rmin:08X}"
            f"{namesize:08X}"
            f"{0:08X}"
        )
        out.write(header_str.encode("ascii"))
        out.write(name_bytes)

        head_pad = (4 - ((110 + namesize) % 4)) % 4
        if head_pad:
            out.write(b"\x00" * head_pad)

        if filesize > 0:
            out.write(e.data)
            file_pad = (4 - (filesize % 4)) % 4
            if file_pad:
                out.write(b"\x00" * file_pad)

    # Append TRAILER!!!
    trailer_name = b"TRAILER!!!\x00"
    t_namesize = len(trailer_name)
    trailer_header = (
        f"070701"
        f"{0:08X}{0:08X}{0:08X}{0:08X}{1:08X}{0:08X}{0:08X}"
        f"{0:08X}{0:08X}{0:08X}{0:08X}{t_namesize:08X}{0:08X}"
    )
    out.write(trailer_header.encode("ascii"))
    out.write(trailer_name)
    t_pad = (4 - ((110 + t_namesize) % 4)) % 4
    if t_pad:
        out.write(b"\x00" * t_pad)

    # Pad to 512-byte block boundary
    total = out.tell()
    remainder = total % 512
    if remainder != 0:
        out.write(b"\x00" * (512 - remainder))

    return out.getvalue()


class IsoInspector:
    """Inspects and parses boot structures in ISO9660 hybrid images."""

    def __init__(self, iso_path: str | Path):
        self.iso_path = Path(iso_path)
        if not self.iso_path.is_file():
            raise FileNotFoundError(f"ISO file not found: {self.iso_path}")
        self.file_size = self.iso_path.stat().st_size
        self._inspect()

    def _inspect(self) -> None:
        with open(self.iso_path, "rb") as f:
            f.seek(16 * 2048)
            pvd = f.read(2048)
            self.volume_id = pvd[40:72].decode("ascii", errors="ignore").strip()
            self.system_id = pvd[8:40].decode("ascii", errors="ignore").strip()

            root_dir_record = pvd[156:190]
            root_sector = int.from_bytes(root_dir_record[2:6], "little")
            root_len = int.from_bytes(root_dir_record[10:14], "little")

            self.entries: dict[str, dict[str, Any]] = {}
            self._scan_dir(f, root_sector, root_len, "")

    def _scan_dir(self, f: Any, sector: int, length: int, prefix: str) -> None:
        f.seek(sector * 2048)
        data = f.read(length)
        pos = 0
        while pos < len(data):
            rec_len = data[pos]
            if rec_len == 0:
                pos += 1
                continue
            rec = data[pos : pos + rec_len]
            sec_loc = int.from_bytes(rec[2:6], "little")
            file_len = int.from_bytes(rec[10:14], "little")
            flags = rec[25]
            name_len = rec[32]
            name = rec[33 : 33 + name_len].decode("latin1").split(";")[0].rstrip(".")

            is_dir = bool(flags & 2)
            if name and name not in ("\x00", "\x01"):
                full_path = f"{prefix}/{name}" if prefix else name
                self.entries[full_path] = {
                    "name": name,
                    "full_path": full_path,
                    "is_dir": is_dir,
                    "sector": sec_loc,
                    "offset": sec_loc * 2048,
                    "length": file_len,
                }
                if is_dir and sec_loc != sector:
                    # Avoid infinite loops on current/parent dir records
                    cur_pos = f.tell()
                    self._scan_dir(f, sec_loc, min(file_len, 4096), full_path)
                    f.seek(cur_pos)

            pos += rec_len

    @staticmethod
    def _normalize_iso_path(p: str) -> str:
        p = p.strip("/").upper()
        if ";" in p:
            p = p.split(";")[0]
        return p.rstrip(".")

    def get_file_bytes(self, path: str) -> bytes:
        norm = self._normalize_iso_path(path)
        match = None
        for k, v in self.entries.items():
            k_norm = self._normalize_iso_path(k)
            if k_norm == norm or k_norm.endswith("/" + norm):
                match = v
                break
        if not match:
            raise KeyError(f"File {path!r} not found in ISO. Available: {list(self.entries.keys())}")
        with open(self.iso_path, "rb") as f:
            f.seek(match["offset"])
            return f.read(match["length"])


class EvoForge:
    """The master builder and orchestrator for EvoCore appliances."""

    def __init__(self, evoloop_root: Path | None = None):
        self.root = evoloop_root or Path(__file__).resolve().parent

    def inspect(self, iso_path: str | Path) -> dict[str, Any]:
        """Performs hardware, kernel, and initramfs audit on a base Tiny Core ISO."""
        inspector = IsoInspector(iso_path)
        sha256 = hashlib.sha256(Path(iso_path).read_bytes()).hexdigest()

        # Locate kernel & initramfs
        kernel_info = None
        initrd_info = None
        for k, v in inspector.entries.items():
            u = k.upper()
            if "VMLINUZ" in u:
                kernel_info = v
            if "CORE.GZ" in u or "TINYCORE.GZ" in u:
                initrd_info = v

        return {
            "iso_path": str(iso_path),
            "file_size_mb": round(inspector.file_size / (1024 * 1024), 2),
            "sha256": sha256,
            "volume_id": inspector.volume_id,
            "system_id": inspector.system_id,
            "kernel_detected": kernel_info,
            "initrd_detected": initrd_info,
            "total_files": len(inspector.entries),
            "file_list": sorted(list(inspector.entries.keys())),
        }

    def remaster_initrd(
        self,
        base_core_gz: bytes,
        overlay_dir: Path | None = None,
        supervisor_dir: Path | None = None,
        profile_data: dict[str, Any] | None = None,
        embed_evolab: bool = True,
    ) -> bytes:
        """Decompresses base initramfs, injects EvoCore overlay & supervisor, and repacks."""
        with gzip.GzipFile(fileobj=io.BytesIO(base_core_gz)) as gz:
            raw_cpio = gz.read()

        entries = read_cpio_archive(raw_cpio)
        entry_map = {e.name: e for e in entries}

        def add_entry_with_parents(rel_path: str, entry: CpioEntry) -> None:
            parts = rel_path.strip("/").split("/")
            cur = ""
            for p in parts[:-1]:
                cur = f"{cur}/{p}" if cur else p
                if cur not in entry_map:
                    entry_map[cur] = CpioEntry(
                        name=cur,
                        mode=0o040755,
                        uid=0,
                        gid=0,
                        nlink=2,
                        mtime=entry.mtime,
                        data=b"",
                    )
            entry_map[rel_path] = entry

        # 1. Inject Overlay Files
        if overlay_dir and overlay_dir.is_dir():
            for p in overlay_dir.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(overlay_dir).as_posix()
                    data = p.read_bytes()
                    if rel.endswith((".sh", ".conf", ".py", ".txt", ".json")):
                        data = data.replace(b"\r\n", b"\n")
                    mode = 0o100755 if rel.endswith(".sh") else 0o100644
                    add_entry_with_parents(rel, CpioEntry(name=rel, mode=mode, data=data))

        # 2. Inject Supervisor
        s_dir = supervisor_dir or (self.root / "supervisor")
        if s_dir.is_dir():
            for p in s_dir.rglob("*"):
                if p.is_file() and not p.name.endswith(".pyc"):
                    rel = "opt/evocore/" + p.relative_to(s_dir).as_posix()
                    data = p.read_bytes()
                    if rel.endswith((".sh", ".conf", ".py", ".txt", ".json")):
                        data = data.replace(b"\r\n", b"\n")
                    mode = 0o100755 if rel.endswith(".sh") or rel.endswith(".py") else 0o100644
                    add_entry_with_parents(rel, CpioEntry(name=rel, mode=mode, data=data))

        # 3. Inject Embedded Experiment Specification
        if profile_data and "experiment" in profile_data:
            exp_bytes = json.dumps(profile_data["experiment"], indent=2).encode("utf-8")
            add_entry_with_parents("opt/evocore/experiment.json", CpioEntry(
                name="opt/evocore/experiment.json",
                mode=0o100644,
                data=exp_bytes,
            ))

        # 4. Inject Full Darwin-Evolab Kernel
        if embed_evolab:
            evolab_src = self.root.parent / "src" / "evolab"
            if evolab_src.is_dir():
                for src_p in evolab_src.rglob("*.py"):
                    rel_p = src_p.relative_to(evolab_src).as_posix()
                    rel = f"opt/evocore/evolab/{rel_p}"
                    data = src_p.read_bytes().replace(b"\r\n", b"\n")
                    add_entry_with_parents(rel, CpioEntry(name=rel, mode=0o100644, data=data))

        # Ensure critical character device nodes are never corrupted
        if "dev/null" in entry_map:
            entry_map["dev/null"].rmaj = 1
            entry_map["dev/null"].rmin = 3
        if "dev/console" in entry_map:
            entry_map["dev/console"].rmaj = 5
            entry_map["dev/console"].rmin = 1
        if "dev/zero" in entry_map:
            entry_map["dev/zero"].rmaj = 1
            entry_map["dev/zero"].rmin = 5

        # Sort entries so parent directories are serialized before their children
        sorted_entries = sorted(entry_map.values(), key=lambda e: (e.name.count("/"), e.name))

        # Serialize modified CPIO
        new_cpio = write_cpio_archive(sorted_entries)

        # Compress to new GZ
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=int(time.time())) as gz_out:
            gz_out.write(new_cpio)

        return buf.getvalue()

    def build_profile(
        self,
        profile_name: str = "minimal",
        base_iso: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Builds remastered EvoCore deployment bundle matching the specified declarative profile."""
        t0 = time.time()
        prof_file = self.root / "profiles" / f"{profile_name}.json"
        if not prof_file.is_file():
            raise FileNotFoundError(f"Profile configuration {profile_name!r} not found at {prof_file}")

        profile = json.loads(prof_file.read_text(encoding="utf-8"))
        iso_source = Path(base_iso or (self.root / "TinyCore-current.iso"))
        out_root = Path(output_dir or (self.root / "output" / profile_name))
        out_root.mkdir(parents=True, exist_ok=True)

        inspector = IsoInspector(iso_source)

        # Extract base kernel and initramfs
        vmlinuz_bytes = inspector.get_file_bytes("BOOT/VMLINUZ")
        core_gz_bytes = inspector.get_file_bytes("BOOT/CORE.GZ")

        # Remaster initramfs with EvoCore supervisor & overlay
        overlay_dir = self.root / "overlay"
        supervisor_dir = self.root / "supervisor"
        remastered_initrd = self.remaster_initrd(
            base_core_gz=core_gz_bytes,
            overlay_dir=overlay_dir,
            supervisor_dir=supervisor_dir,
            profile_data=profile,
            embed_evolab=True,
        )

        # Check if Python payload exists to embed
        py_payload_p = self.root / "python_payload.cpio.gz"
        if py_payload_p.exists():
            print(f"[EvoForge] Embedding Python 3 runtime payload ({py_payload_p.stat().st_size // (1024*1024)} MB)...")
            remastered_initrd = remastered_initrd + py_payload_p.read_bytes()

        # Write output boot files
        boot_dir = out_root / "boot"
        boot_dir.mkdir(parents=True, exist_ok=True)

        vmlinuz_out = boot_dir / "vmlinuz"
        vmlinuz_out.write_bytes(vmlinuz_bytes)

        initrd_out = boot_dir / "core.gz"
        initrd_out.write_bytes(remastered_initrd)

        # Generate ISOLINUX boot configuration
        isolinux_cfg = f"""DEFAULT evocore_lab
UI menu.c32
PROMPT 0
TIMEOUT 50
ONTIMEOUT evocore_lab

MENU TITLE Darwin-Evolab Experimental Linux (EvoCore v{EVOCORE_VERSION})
MENU MARGIN 10
MENU ROWS 6

LABEL evocore_lab
MENU LABEL 1. EvoCore [Laboratory Mode - Autonomous Experiment]
TEXT HELP
Boots into RAM, executes registered scientific experiment, emits signed manifest.
ENDTEXT
KERNEL /boot/vmlinuz
INITRD /boot/core.gz
APPEND loglevel=3 quiet evomode=lab console=tty0 console=ttyS0,115200

LABEL evocore_research
MENU LABEL 2. EvoCore [Research Mode - Interactive REPL & Shell]
TEXT HELP
Boots into RAM and launches interactive shell with Evolab environment pre-loaded.
ENDTEXT
KERNEL /boot/vmlinuz
INITRD /boot/core.gz
APPEND loglevel=3 evomode=research console=tty0 console=ttyS0,115200
"""
        isolinux_dir = boot_dir / "isolinux"
        isolinux_dir.mkdir(parents=True, exist_ok=True)
        (isolinux_dir / "isolinux.cfg").write_text(isolinux_cfg, encoding="utf-8")

        # Copy bootloader files from base ISO
        for bl_file in ["ISOLINUX.BIN", "BOOT.CAT", "MENU.C32"]:
            try:
                b_data = inspector.get_file_bytes(f"BOOT/ISOLINUX/{bl_file}")
                (isolinux_dir / bl_file.lower()).write_bytes(b_data)
            except Exception:
                pass

        # Generate standalone bootable ISO
        iso_out = out_root / f"EvoCore-{profile_name}.iso"
        self.remaster_iso(
            base_iso=iso_source,
            output_iso=iso_out,
            new_initrd_bytes=remastered_initrd,
            new_isolinux_cfg=isolinux_cfg,
        )

        # Write build attestation manifest
        build_time = time.time() - t0
        manifest = {
            "appliance": "EvoCore",
            "version": EVOCORE_VERSION,
            "profile": profile_name,
            "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "build_duration_seconds": round(build_time, 2),
            "base_iso": str(iso_source),
            "artifacts": {
                "vmlinuz_size": len(vmlinuz_bytes),
                "vmlinuz_sha256": hashlib.sha256(vmlinuz_bytes).hexdigest(),
                "initrd_size": len(remastered_initrd),
                "initrd_sha256": hashlib.sha256(remastered_initrd).hexdigest(),
                "iso_path": str(iso_out),
                "iso_size": iso_out.stat().st_size,
                "iso_sha256": hashlib.sha256(iso_out.read_bytes()).hexdigest(),
            },
            "profile_specification": profile,
            "output_directory": str(out_root),
        }

        manifest_path = out_root / "build_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        return manifest

    def remaster_iso(
        self,
        base_iso: Path | str,
        output_iso: Path | str,
        new_initrd_bytes: bytes,
        new_isolinux_cfg: str,
    ) -> Path:
        """Generates a bootable hybrid ISO9660 image by injecting new initrd and bootloader config."""
        base_path = Path(base_iso)
        out_path = Path(output_iso)
        data = bytearray(base_path.read_bytes())

        # Pad existing image to 2048-byte sector boundary
        if len(data) % 2048 != 0:
            data.extend(b"\x00" * (2048 - (len(data) % 2048)))

        # Append new initrd (core.gz)
        initrd_lba = len(data) // 2048
        initrd_len = len(new_initrd_bytes)
        data.extend(new_initrd_bytes)
        if len(data) % 2048 != 0:
            data.extend(b"\x00" * (2048 - (len(data) % 2048)))

        # Append new isolinux.cfg
        cfg_bytes = new_isolinux_cfg.encode("utf-8")
        cfg_lba = len(data) // 2048
        cfg_len = len(cfg_bytes)
        data.extend(cfg_bytes)
        if len(data) % 2048 != 0:
            data.extend(b"\x00" * (2048 - (len(data) % 2048)))

        total_sectors = len(data) // 2048

        # Update Primary Volume Descriptor (Sector 16, offset 16*2048 + 80 and 84)
        pvd_offset = 16 * 2048
        data[pvd_offset + 80 : pvd_offset + 84] = struct.pack("<I", total_sectors)
        data[pvd_offset + 84 : pvd_offset + 88] = struct.pack(">I", total_sectors)

        # Update CORE.GZ directory record
        pos1 = data.find(b"CORE.GZ")
        if pos1 != -1:
            rec1 = pos1 - 33
            data[rec1 + 2 : rec1 + 6] = struct.pack("<I", initrd_lba)
            data[rec1 + 6 : rec1 + 10] = struct.pack(">I", initrd_lba)
            data[rec1 + 10 : rec1 + 14] = struct.pack("<I", initrd_len)
            data[rec1 + 14 : rec1 + 18] = struct.pack(">I", initrd_len)

        # Update ISOLINUX.CFG directory record
        pos2 = data.find(b"ISOLINUX.CFG")
        if pos2 != -1:
            rec2 = pos2 - 33
            data[rec2 + 2 : rec2 + 6] = struct.pack("<I", cfg_lba)
            data[rec2 + 6 : rec2 + 10] = struct.pack(">I", cfg_lba)
            data[rec2 + 10 : rec2 + 14] = struct.pack("<I", cfg_len)
            data[rec2 + 14 : rec2 + 18] = struct.pack(">I", cfg_len)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EvoForge — EvoCore Appliance Generator")
    sub = parser.add_subparsers(dest="command", required=True)

    # Subcommand: inspect
    p_insp = sub.add_parser("inspect", help="Inspect an existing Tiny Core or EvoCore ISO")
    p_insp.add_argument("iso", type=str, help="Path to ISO image")

    # Subcommand: build
    p_bld = sub.add_parser("build", help="Build remastered EvoCore boot bundle from profile")
    p_bld.add_argument("--profile", default="minimal", choices=["minimal", "symbolic", "eda"], help="Profile name")
    p_bld.add_argument("--base", default=None, help="Base ISO image (defaults to TinyCore-current.iso)")
    p_bld.add_argument("--output-dir", default=None, help="Output destination")

    # Subcommand: test-supervisor
    p_sup = sub.add_parser("test-supervisor", help="Executes the supervisor in-process for testing")
    p_sup.add_argument("--mode", default="lab", choices=["lab", "research"])

    args = parser.parse_args(argv)
    forge = EvoForge()

    if args.command == "inspect":
        res = forge.inspect(args.iso)
        print(f"=== EvoForge Inspection Report for {args.iso} ===")
        print(f"  Volume ID        : {res['volume_id']}")
        print(f"  ISO Size (MB)    : {res['file_size_mb']}")
        print(f"  ISO SHA-256      : {res['sha256']}")
        print(f"  Kernel Detected  : {res['kernel_detected']['name'] if res['kernel_detected'] else 'None'}")
        print(f"  InitRD Detected  : {res['initrd_detected']['name'] if res['initrd_detected'] else 'None'}")
        print(f"  Total Files      : {res['total_files']}")

    elif args.command == "build":
        print(f"[EvoForge] Building EvoCore appliance for profile: {args.profile}...")
        manifest = forge.build_profile(profile_name=args.profile, base_iso=args.base, output_dir=args.output_dir)
        print(f"[EvoForge] Build completed successfully in {manifest['build_duration_seconds']}s!")
        print(f"           Kernel SHA-256 : {manifest['artifacts']['vmlinuz_sha256'][:16]}...")
        print(f"           InitRD SHA-256 : {manifest['artifacts']['initrd_sha256'][:16]}... ({manifest['artifacts']['initrd_size']} bytes)")
        print(f"           Output Root    : {manifest['output_directory']}")
        print(f"           Manifest File  : {Path(manifest['output_directory']) / 'build_manifest.json'}")

    elif args.command == "test-supervisor":
        from supervisor.supervisor import main as sup_main
        return sup_main(["--mode", args.mode, "--output-dir", "EvoCore/output/test_run"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
