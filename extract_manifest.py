"""extract_manifest.py — Extracts cryptographic evidence manifest from raw serial log."""
import json
import sys
from pathlib import Path


def extract(log_file: Path, out_file: Path) -> bool:
    if not log_file.is_file():
        return False
    text = log_file.read_text(encoding="utf-8", errors="replace")
    start_tag = "=== BEGIN EVOCORE EVIDENCE MANIFEST ==="
    end_tag = "=== END EVOCORE EVIDENCE MANIFEST ==="
    start_idx = text.find(start_tag)
    end_idx = text.find(end_tag)
    if start_idx == -1 or end_idx == -1:
        return False
    json_str = text[start_idx + len(start_tag) : end_idx].strip()
    try:
        manifest = json.loads(json_str)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    default_log = script_dir / "output" / "last_run.log"
    default_out = script_dir / "output" / "evidence_manifest.json"

    log_p = Path(sys.argv[1]) if len(sys.argv) > 1 else default_log
    out_p = Path(sys.argv[2]) if len(sys.argv) > 2 else default_out

    if extract(log_p, out_p):
        print(f"[OK] Evidence manifest extracted: {out_p}")
    else:
        print("[!] Evidence manifest markers not found in log.")
