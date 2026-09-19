"""End-to-end bridge test against a synthetic repository (no freqtrade, no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation import bridge as bridge_mod
from automation import validation as val

pytestmark = pytest.mark.bridge


def _write_min_repo(root: Path) -> None:
    mece = root / ".mece"
    cells = mece / "cells"
    results = root / "research" / "experiment_results"
    reports = root / "reports"
    for directory in (cells, results, reports):
        directory.mkdir(parents=True, exist_ok=True)
    (mece / "PHASE_GATE.json").write_text(
        json.dumps(
            {
                "phase": "PHASE2",
                "allow_new_experiments": False,
                "stop_after_phase_completion": True,
            }
        ),
        encoding="utf-8",
    )
    (mece / "WAVE.md").write_text("# wave\n", encoding="utf-8")
    (mece / "SYNTHESIS.md").write_text(
        "# SYNTHESIS\n\n## 7. Recommended next step (exact)\n\n"
        "1. Implement and run the frozen walk-forward harness.\n\n## 8. Cell reports\n",
        encoding="utf-8",
    )
    for index in (1, 2, 3):
        cell = cells / f"CELL-00{index}"
        cell.mkdir(parents=True, exist_ok=True)
        (cell / "REPORT.md").write_text("# report\n", encoding="utf-8")
    for exp_id in val.ARTIFACT_IDS:
        (results / f"{exp_id}.json").write_text(
            json.dumps(
                {
                    "experiment_id": exp_id,
                    "status": "COMPLETED",
                    "verdict": "FAIL",
                    "funding_applied": True,
                    "production_strategy_changed": False,
                }
            ),
            encoding="utf-8",
        )
        (results / f"{exp_id}.md").write_text("Status: FAIL\n", encoding="utf-8")
    (reports / "README.md").write_text("# reports\n", encoding="utf-8")


def test_bridge_end_to_end_writes_report_and_proposal(tmp_path, capsys) -> None:
    _write_min_repo(tmp_path)
    code = bridge_mod.main(["--root", str(tmp_path), "--run-id", "it_bridge", "--json"])
    assert code == 0
    emitted = capsys.readouterr().out
    assert "it_bridge" in emitted
    report_path = tmp_path / "reports" / "it_bridge_REPORT.md"
    assert report_path.is_file()
    next_task = tmp_path / ".mece" / "NEXT_TASK.md"
    assert next_task.is_file()
    text = next_task.read_text(encoding="utf-8")
    assert "PROPOSAL ONLY" in text
    assert "walk-forward harness" in text
    assert "NOT EXECUTED" in text


def test_bridge_dry_run_writes_nothing(tmp_path) -> None:
    _write_min_repo(tmp_path)
    code = bridge_mod.main(["--root", str(tmp_path), "--dry-run", "--json"])
    assert code == 0
    assert not (tmp_path / "reports" / "phase2_bridge_REPORT.md").exists()
    assert not (tmp_path / ".mece" / "NEXT_TASK.md").exists()


def test_bridge_fails_on_broken_gate(tmp_path, capsys) -> None:
    root = tmp_path
    (root / ".mece").mkdir(parents=True)
    (root / ".mece" / "PHASE_GATE.json").write_text("{ not json", encoding="utf-8")
    code = bridge_mod.main(["--root", str(root), "--json"])
    assert code == bridge_mod.EXIT_CONFIG


def test_bridge_with_crew_invokes_crew_stage(tmp_path, monkeypatch) -> None:
    _write_min_repo(tmp_path)
    called: dict[str, bool] = {}

    def fake_run_crew(cfg, **kwargs):
        called["invoked"] = True
        return bridge_mod.crew_mod.CrewRunResult(
            executed=True, skipped=False, reason="crew executed", output="ok"
        )

    monkeypatch.setattr(bridge_mod.crew_mod, "run_crew", fake_run_crew)
    code = bridge_mod.main(
        ["--root", str(tmp_path), "--run-id", "crew_it", "--with-crew", "--json"]
    )
    assert code == 0
    assert called.get("invoked") is True


def test_bridge_without_crew_skips_stage(tmp_path, monkeypatch) -> None:
    _write_min_repo(tmp_path)
    called: dict[str, bool] = {}

    def fake_run_crew(cfg, **kwargs):
        called["invoked"] = True
        return bridge_mod.crew_mod.CrewRunResult(True, False, "crew executed", "ok")

    monkeypatch.setattr(bridge_mod.crew_mod, "run_crew", fake_run_crew)
    code = bridge_mod.main(["--root", str(tmp_path), "--run-id", "nocrew", "--json"])
    assert code == 0
    assert "invoked" not in called


def test_bridge_rejects_unsafe_run_id(tmp_path) -> None:
    _write_min_repo(tmp_path)
    code = bridge_mod.main(["--root", str(tmp_path), "--run-id", "../escape", "--json"])
    assert code == bridge_mod.EXIT_CONFIG
    assert not (tmp_path.parent / "escape_REPORT.md").exists()
