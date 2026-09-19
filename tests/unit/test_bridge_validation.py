"""Unit tests for the bridge validation gates."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from automation import validation as val

pytestmark = pytest.mark.bridge


def _completed(stdout: str = "", stderr: str = "", code: int = 0):
    return subprocess.CompletedProcess(args=["git"], returncode=code, stdout=stdout, stderr=stderr)


def test_production_changes_clean() -> None:
    lines, note = val.production_changes(Path("."), git_runner=lambda argv, cwd: _completed())
    assert lines == []
    assert note == "clean"


def test_production_changes_dirty() -> None:
    dirty = " M user_data/strategies/shared/pa_risk.py\n"
    check = val.check_production_untouched(
        Path("."), git_runner=lambda argv, cwd: _completed(stdout=dirty)
    )
    assert check.ok is False


def test_production_check_tolerates_non_repo() -> None:
    check = val.check_production_untouched(
        Path("."),
        git_runner=lambda argv, cwd: _completed(stderr="fatal: not a git repository", code=128),
    )
    assert check.ok is True


def _write_min_artifacts(root: Path) -> Path:
    results = root / "research" / "experiment_results"
    results.mkdir(parents=True)
    for exp_id in val.ARTIFACT_IDS:
        payload = {
            "experiment_id": exp_id,
            "status": "COMPLETED",
            "verdict": "FAIL",
            "funding_applied": True,
            "production_strategy_changed": False,
        }
        (results / f"{exp_id}.json").write_text(json.dumps(payload), encoding="utf-8")
        (results / f"{exp_id}.md").write_text("Status: FAIL\n", encoding="utf-8")
    return results


def test_json_artifacts_consistent(tmp_path) -> None:
    _write_min_artifacts(tmp_path)
    assert val.check_json_artifacts(tmp_path).ok is True


def test_json_artifacts_flag_funding_defect(tmp_path) -> None:
    results = _write_min_artifacts(tmp_path)
    target = results / f"{val.ARTIFACT_IDS[0]}.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["funding_applied"] = False
    target.write_text(json.dumps(payload), encoding="utf-8")
    assert val.check_json_artifacts(tmp_path).ok is False


def test_json_artifacts_flag_verdict_mismatch(tmp_path) -> None:
    results = _write_min_artifacts(tmp_path)
    target = results / f"{val.ARTIFACT_IDS[1]}.json"
    target.write_text(
        json.dumps({"experiment_id": val.ARTIFACT_IDS[1], "verdict": "PASS"}),
        encoding="utf-8",
    )
    assert val.check_json_artifacts(tmp_path).ok is False


def test_snapshot_ignores_generated_utc_only(tmp_path) -> None:
    results = _write_min_artifacts(tmp_path)
    target = results / f"{val.ARTIFACT_IDS[0]}.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["generated_utc"] = "2026-01-01T00:00:00+00:00"
    target.write_text(json.dumps(payload), encoding="utf-8")
    before = val.snapshot_results(tmp_path)
    payload["generated_utc"] = "2026-09-18T00:00:00+00:00"
    target.write_text(json.dumps(payload), encoding="utf-8")
    unchanged, changed = val.results_unchanged(before, val.snapshot_results(tmp_path))
    assert unchanged and changed == []


def test_snapshot_results_detects_substantive_change(tmp_path) -> None:
    results = _write_min_artifacts(tmp_path)
    before = val.snapshot_results(tmp_path)
    unchanged, changed = val.results_unchanged(before, val.snapshot_results(tmp_path))
    assert unchanged and changed == []
    target = results / f"{val.ARTIFACT_IDS[0]}.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["verdict"] = "PASS"
    target.write_text(json.dumps(payload), encoding="utf-8")
    unchanged, changed = val.results_unchanged(before, val.snapshot_results(tmp_path))
    assert not unchanged
    assert changed


def test_bridge_safety_flags_dangerous_pattern(tmp_path) -> None:
    automation = tmp_path / "automation"
    automation.mkdir()
    (automation / "bridge.py").write_text("import os\nos.system('x')\n", encoding="utf-8")
    assert val.check_bridge_safety(tmp_path).ok is False


def test_bridge_safety_clean(tmp_path) -> None:
    automation = tmp_path / "automation"
    automation.mkdir()
    (automation / "bridge.py").write_text("print('ok')\n", encoding="utf-8")
    assert val.check_bridge_safety(tmp_path).ok is True


def test_real_repo_validation_passes() -> None:
    result = val.run_validation()
    assert result.ok, result.failures


def test_check_gate_present_real_repo() -> None:
    assert val.check_gate_present().ok is True


def test_required_artifacts_real_repo() -> None:
    assert val.check_required_artifacts().ok is True
