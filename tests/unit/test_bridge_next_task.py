"""Unit tests for the proposal-only next-task writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import next_task
from automation.config import BridgeConfig
from automation.gate import PhaseGate

pytestmark = pytest.mark.bridge

SAMPLE = """# SYNTHESIS

## 7. Recommended next step (exact)

1. Implement the walk-forward harness.
2. Then run P3-EXP-006.
3. Obtain a fresh holdout.

## 8. Cell reports

- nothing
"""


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


def _gate(root: Path) -> PhaseGate:
    return PhaseGate(
        phase="PHASE2",
        allow_new_experiments=False,
        stop_after_phase_completion=True,
        path=root / "PHASE_GATE.json",
        raw={},
    )


def test_extract_synthesis_next_steps() -> None:
    assert next_task.extract_synthesis_next_steps(SAMPLE) == [
        "Implement the walk-forward harness.",
        "Then run P3-EXP-006.",
        "Obtain a fresh holdout.",
    ]


def test_extract_missing_section() -> None:
    assert next_task.extract_synthesis_next_steps("# nothing here") == []


def test_propose_writes_proposal_only(tmp_path) -> None:
    mece = tmp_path / ".mece"
    mece.mkdir(parents=True)
    (mece / "SYNTHESIS.md").write_text(SAMPLE, encoding="utf-8")
    result = next_task.propose_next_task(_cfg(tmp_path), _gate(tmp_path), "r1")
    assert result.written is True
    assert result.executed is False
    text = result.path.read_text(encoding="utf-8")
    assert "PROPOSAL ONLY" in text
    assert "Implement the walk-forward harness." in text
    assert "NOT EXECUTED" in text


def test_propose_refuses_overwrite_without_force(tmp_path) -> None:
    mece = tmp_path / ".mece"
    mece.mkdir(parents=True)
    (mece / "SYNTHESIS.md").write_text(SAMPLE, encoding="utf-8")
    first = next_task.propose_next_task(_cfg(tmp_path), _gate(tmp_path), "r1")
    assert first.written is True
    second = next_task.propose_next_task(_cfg(tmp_path), _gate(tmp_path), "r2")
    assert second.written is False
    forced = next_task.propose_next_task(_cfg(tmp_path), _gate(tmp_path), "r3", force=True)
    assert forced.written is True
    assert "r3" in forced.path.read_text(encoding="utf-8")
