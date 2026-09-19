"""Unit tests for the fail-closed phase gate."""

from __future__ import annotations

import json

import pytest

from automation import gate as gate_mod

pytestmark = pytest.mark.bridge


def test_real_gate_is_closed() -> None:
    gate = gate_mod.load_gate()
    assert gate.phase == "PHASE2"
    assert gate.allow_new_experiments is False
    assert gate.stop_after_phase_completion is True
    assert gate_mod.experiment_execution_allowed(gate) is False


def test_gate_can_authorise_execution(tmp_path) -> None:
    path = tmp_path / "PHASE_GATE.json"
    path.write_text(
        json.dumps(
            {
                "phase": "PHASE9",
                "allow_new_experiments": True,
                "stop_after_phase_completion": False,
            }
        ),
        encoding="utf-8",
    )
    gate = gate_mod.load_gate(path)
    assert gate_mod.experiment_execution_allowed(gate) is True


def test_stop_after_completion_blocks_even_when_allowed(tmp_path) -> None:
    path = tmp_path / "PHASE_GATE.json"
    path.write_text(
        json.dumps(
            {
                "phase": "PHASE9",
                "allow_new_experiments": True,
                "stop_after_phase_completion": True,
            }
        ),
        encoding="utf-8",
    )
    gate = gate_mod.load_gate(path)
    assert gate_mod.experiment_execution_allowed(gate) is False


@pytest.mark.parametrize(
    "payload",
    [
        "not json at all",
        "[]",
        json.dumps({"allow_new_experiments": True}),
        json.dumps({"allow_new_experiments": "yes", "stop_after_phase_completion": False}),
        json.dumps({"allow_new_experiments": True, "stop_after_phase_completion": 1}),
    ],
)
def test_malformed_gate_fails_closed(tmp_path, payload: str) -> None:
    path = tmp_path / "PHASE_GATE.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(gate_mod.GateError):
        gate_mod.load_gate(path)


def test_missing_gate_fails_closed(tmp_path) -> None:
    with pytest.raises(gate_mod.GateError):
        gate_mod.load_gate(tmp_path / "does_not_exist.json")
