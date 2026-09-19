"""Phase-gate reader for the automation bridge.

``.mece/PHASE_GATE.json`` is authoritative. The bridge fails closed: a missing,
malformed or partially-typed gate is an error, never an implicit "allow".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from automation.config import GATE_FILE


class GateError(RuntimeError):
    """Raised when the phase gate is missing or malformed (fail-closed)."""


@dataclass(frozen=True)
class PhaseGate:
    """Immutable snapshot of the phase gate."""

    phase: str
    allow_new_experiments: bool
    stop_after_phase_completion: bool
    path: Path
    raw: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """
        Return a JSON-serialisable summary.

        :return: Gate summary dictionary.
        """
        return {
            "phase": self.phase,
            "allow_new_experiments": self.allow_new_experiments,
            "stop_after_phase_completion": self.stop_after_phase_completion,
            "path": str(self.path),
        }


def load_gate(path: Path | str | None = None) -> PhaseGate:
    """
    Load and validate the phase gate.

    :param path: Override path (defaults to ``.mece/PHASE_GATE.json``).
    :return: Validated :class:`PhaseGate`.
    :raises GateError: When the gate is missing or malformed.
    """
    target = Path(path) if path is not None else GATE_FILE
    if not target.is_file():
        raise GateError(f"phase gate not found: {target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateError(f"phase gate is not valid JSON: {target}: {exc}") from exc
    if not isinstance(data, dict):
        raise GateError(f"phase gate must be a JSON object: {target}")
    for key in ("allow_new_experiments", "stop_after_phase_completion"):
        if not isinstance(data.get(key), bool):
            raise GateError(f"phase gate missing boolean '{key}': {target}")
    return PhaseGate(
        phase=str(data.get("phase", "UNKNOWN")),
        allow_new_experiments=data["allow_new_experiments"],
        stop_after_phase_completion=data["stop_after_phase_completion"],
        path=target,
        raw=dict(data),
    )


def experiment_execution_allowed(gate: PhaseGate) -> bool:
    """
    Report whether a *new experiment* may be executed.

    Both conditions must hold: experiments enabled and no stop-after-completion.

    :param gate: Phase gate snapshot.
    :return: True only when execution is explicitly authorised.
    """
    return gate.allow_new_experiments and not gate.stop_after_phase_completion
