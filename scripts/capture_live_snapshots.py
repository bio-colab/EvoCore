"""capture_live_snapshots.py — Automates live QEMU VGA framebuffer capture for documentation."""
from __future__ import annotations

import socket
import subprocess
import time
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = REPO_ROOT / "docs" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

QEMU = r"C:\Program Files\qemu\qemu-system-x86_64.exe"
VMLINUZ = REPO_ROOT / "output" / "minimal" / "boot" / "vmlinuz"
CORE_GZ = REPO_ROOT / "output" / "minimal" / "boot" / "core.gz"
ISO_PATH = REPO_ROOT / "output" / "minimal" / "EvoCore-minimal.iso"


def capture_screendump(cmd: list[str], port: int, wait_boot_seconds: float, output_png: Path) -> bool:
    print(f"\n[*] Launching QEMU for {output_png.name} (waiting {wait_boot_seconds}s)...")
    cmd = list(cmd) + ["-display", "none", "-monitor", f"tcp:127.0.0.1:{port},server,nowait"]
    proc = subprocess.Popen(cmd)

    try:
        time.sleep(wait_boot_seconds)
        s = socket.socket()
        s.settimeout(5)
        s.connect(("127.0.0.1", port))
        time.sleep(0.5)
        try:
            s.recv(1024)
        except Exception:
            pass

        ppm_path = output_png.with_suffix(".ppm")
        print(f"[*] Sending screendump to {ppm_path.name}...")
        s.sendall(f"screendump {ppm_path.as_posix()}\n".encode("ascii"))
        time.sleep(1.0)
        try:
            s.sendall(b"quit\n")
        except Exception:
            pass
        s.close()

        # Wait a moment for QEMU to flush file
        time.sleep(1.0)

        if ppm_path.is_file() and ppm_path.stat().st_size > 0:
            img = Image.open(ppm_path)
            img.save(output_png)
            ppm_path.unlink()
            print(f"[OK] Successfully captured {output_png.name} ({output_png.stat().st_size} bytes, dimensions={img.size})")
            return True
        else:
            print(f"[!] PPM file was not created for {output_png.name}")
            return False

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            proc.kill()


def main():
    print("=== EvoCore Live Snapshot Harvester ===")

    # 1. Capture Full ISO Bootloader
    capture_screendump(
        cmd=[QEMU, "-cdrom", str(ISO_PATH), "-boot", "d", "-m", "512M"],
        port=55551,
        wait_boot_seconds=3.0,
        output_png=IMAGES_DIR / "evocore_iso_boot.png",
    )

    # 2. Capture Research Mode Shell
    capture_screendump(
        cmd=[QEMU, "-kernel", str(VMLINUZ), "-initrd", str(CORE_GZ), "-append", "console=tty0 quiet evomode=research", "-m", "512M"],
        port=55552,
        wait_boot_seconds=18.0,
        output_png=IMAGES_DIR / "evocore_research_mode.png",
    )

    # 3. Capture Laboratory Mode (Discovery & Telemetry)
    capture_screendump(
        cmd=[QEMU, "-kernel", str(VMLINUZ), "-initrd", str(CORE_GZ), "-append", "console=tty0 quiet evomode=lab", "-m", "512M"],
        port=55553,
        wait_boot_seconds=24.0,
        output_png=IMAGES_DIR / "evocore_lab_mode.png",
    )

    print("\n[OK] All snapshot captures completed.")


if __name__ == "__main__":
    main()
