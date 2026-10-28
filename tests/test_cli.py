"""test_cli.py — Comprehensive CliRunner test suite for EvoCore CLI harness."""
from __future__ import annotations

import json
from pathlib import Path
from click.testing import CliRunner

from evocore.cli import main
from evocore.constants import VERSION


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert VERSION in result.output


def test_cli_info_human_and_json():
    runner = CliRunner()

    # Human format
    res_human = runner.invoke(main, ["info"])
    assert res_human.exit_code == 0
    assert "EvoCore Appliance Telemetry" in res_human.output

    # JSON format
    res_json = runner.invoke(main, ["info", "--json"])
    assert res_json.exit_code == 0
    parsed = json.loads(res_json.output)
    assert parsed["status"] == "success"
    assert parsed["data"]["appliance"] == "EvoCore"
    assert parsed["data"]["version"] == VERSION
    assert "qemu" in parsed["data"]


def test_cli_profile_commands():
    runner = CliRunner()

    # profile list JSON
    res = runner.invoke(main, ["profile", "list", "--json"])
    assert res.exit_code == 0
    parsed = json.loads(res.output)
    assert parsed["status"] == "success"
    assert any(p["name"] == "minimal" for p in parsed["data"])

    # profile show minimal JSON
    res_show = runner.invoke(main, ["profile", "show", "minimal", "--json"])
    assert res_show.exit_code == 0
    parsed_show = json.loads(res_show.output)
    assert parsed_show["status"] == "success"
    assert parsed_show["data"]["profile"] == "minimal"

    # profile show nonexistent
    res_err = runner.invoke(main, ["profile", "show", "missing_profile", "--json"])
    assert res_err.exit_code != 0
    parsed_err = json.loads(res_err.output)
    assert parsed_err["status"] == "error"


def test_cli_evidence_workflow(tmp_path: Path):
    runner = CliRunner()

    # Create dummy manifest
    manifest_data = {
        "appliance": "EvoCore",
        "appliance_version": VERSION,
        "timestamp_utc": "2026-10-28 00:00:00",
        "signatures": {
            "specification_sha256": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
            "solution_sha256": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
        },
        "specification": {},
        "solution": {},
    }
    manifest_file = tmp_path / "evidence_manifest.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    # evidence inspect
    res_insp = runner.invoke(main, ["evidence", "inspect", str(manifest_file), "--json"])
    assert res_insp.exit_code == 0
    assert json.loads(res_insp.output)["status"] == "success"

    # evidence verify
    res_ver = runner.invoke(main, ["evidence", "verify", str(manifest_file), "--json"])
    assert res_ver.exit_code == 0
    assert json.loads(res_ver.output)["data"]["valid"] is True

    # evidence bundle
    bundle_file = tmp_path / "test.evobundle"
    res_bun = runner.invoke(main, ["evidence", "bundle", str(manifest_file), "--output", str(bundle_file), "--json"])
    assert res_bun.exit_code == 0
    assert bundle_file.is_file()

    # evidence verify bundle
    res_ver_bun = runner.invoke(main, ["evidence", "verify", str(bundle_file), "--json"])
    assert res_ver_bun.exit_code == 0
    assert json.loads(res_ver_bun.output)["data"]["valid"] is True

    # evidence unpack
    unpack_dir = tmp_path / "unpacked"
    res_unp = runner.invoke(main, ["evidence", "unpack", str(bundle_file), "--dest", str(unpack_dir), "--json"])
    assert res_unp.exit_code == 0
    assert (unpack_dir / "evidence_manifest.json").is_file()


def test_cli_invalid_command():
    runner = CliRunner()
    res = runner.invoke(main, ["unknown_subcmd"])
    assert res.exit_code != 0
