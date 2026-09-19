"""Regression tests for run-id sanitization (path-traversal prevention)."""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import next_task, opencode_client, report
from automation.config import BridgeConfig, sanitize_run_id
from automation.gate import PhaseGate

pytestmark = pytest.mark.bridge


def _cfg(root: Path) -> BridgeConfig:
    return BridgeConfig(
        root=root,
        python="python",
        python_source="test",
        opencode="opencode",
        opencode_source="test",
        opencode_model=None,
        opencode_agent=None,
        timeout_s=5.0,
    )


def _gate() -> PhaseGate:
    return PhaseGate(
        phase="PHASE2",
        allow_new_experiments=False,
        stop_after_phase_completion=True,
        path=Path("g.json"),
        raw={},
    )


@pytest.mark.parametrize("run_id", ["phase2_bridge", "v1.2", "run-1", "a_b.c-d"])
def test_sanitize_accepts_safe_ids(run_id: str) -> None:
    assert sanitize_run_id(run_id) == run_id


@pytest.mark.parametrize(
    "run_id",
    ["..", ".", "", "a/b", "a\\b", "..\\..\\escaped", "with space", "x" * 129],
)
def test_sanitize_rejects_unsafe_ids(run_id: str) -> None:
    with pytest.raises(ValueError):
        sanitize_run_id(run_id)


def test_write_report_rejects_traversal(tmp_path) -> None:
    with pytest.raises(ValueError):
        report.write_report(tmp_path, "..\\..\\escaped", "content")
    assert not (tmp_path.parent / "escaped_REPORT.md").exists()


def test_render_report_rejects_traversal(tmp_path) -> None:
    with pytest.raises(ValueError):
        report.render_report(tmp_path, "../escape", _gate())


def test_opencode_transcript_rejects_traversal(tmp_path) -> None:
    with pytest.raises(ValueError):
        opencode_client.run_opencode(
            _cfg(tmp_path), "prompt", name="bridge_..\\..\\escaped", logs_dir=tmp_path / "logs"
        )


def test_next_task_rejects_traversal(tmp_path) -> None:
    mece = tmp_path / ".mece"
    mece.mkdir(parents=True)
    (mece / "SYNTHESIS.md").write_text("# S\n\n## 7. Next\n\n1. Do it.\n", encoding="utf-8")
    with pytest.raises(ValueError):
        next_task.propose_next_task(_cfg(tmp_path), _gate(), "..\\..\\escaped")
