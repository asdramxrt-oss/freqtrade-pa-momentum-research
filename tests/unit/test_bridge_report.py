"""Unit tests for the deterministic REPORT.md generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import gate as gate_mod
from automation import report
from automation.config import PROJECT_ROOT, BridgeConfig
from automation.validation import Check

pytestmark = pytest.mark.bridge


def _cfg(root: Path) -> BridgeConfig:
    return BridgeConfig(
        root=root,
        python="python",
        python_source="test",
        opencode=None,
        opencode_source="missing",
        opencode_model=None,
        opencode_agent=None,
        timeout_s=1.0,
    )


def test_render_report_is_deterministic() -> None:
    gate = gate_mod.load_gate()
    first = report.render_report(PROJECT_ROOT, "run-x", gate)
    second = report.render_report(PROJECT_ROOT, "run-x", gate)
    assert first == second


def test_render_report_includes_artifacts_and_checks() -> None:
    gate = gate_mod.load_gate()
    text = report.render_report(
        PROJECT_ROOT,
        "run-y",
        gate,
        validation=[Check("production_untouched", True, "clean")],
        next_task_path=PROJECT_ROOT / ".mece" / "NEXT_TASK.md",
    )
    assert "P3-EXP-001" in text
    assert "FAIL" in text
    assert "production_untouched" in text
    assert "PROPOSAL ONLY" in text
    assert "generated_utc" not in text


def test_input_digest_is_stable() -> None:
    assert report.input_digest(PROJECT_ROOT) == report.input_digest(PROJECT_ROOT)


def test_write_report_creates_file(tmp_path) -> None:
    path = report.write_report(tmp_path, "abc", "hello")
    assert path == tmp_path / "reports" / "abc_REPORT.md"
    assert path.read_text(encoding="utf-8") == "hello"


def test_artifact_rows_flag_missing(tmp_path) -> None:
    rows = report.artifact_rows(tmp_path)
    assert len(rows) == 3
    assert all(row.status == "MISSING" for row in rows)


def test_build_report_writes_expected_name(tmp_path) -> None:
    gate = gate_mod.PhaseGate(
        phase="PHASE2",
        allow_new_experiments=False,
        stop_after_phase_completion=True,
        path=tmp_path / "g.json",
        raw={},
    )
    path = report.build_report(_cfg(tmp_path), gate, "z")
    assert path == tmp_path / "reports" / "z_REPORT.md"
    assert path.is_file()
