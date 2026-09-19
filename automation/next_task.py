"""Next-task proposer (proposal only — never an executor).

Reads the existing ``.mece`` research state, the decision log and the experiment
registry, and writes a proposal to ``.mece/NEXT_TASK.md``. It never runs an
experiment, never advances the programme, and refuses to overwrite a human's
file unless explicitly forced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from automation.config import (
    NEXT_TASK_FILE,
    PROJECT_ROOT,
    SYNTHESIS_FILE,
    BridgeConfig,
    sanitize_run_id,
)
from automation.gate import PhaseGate, experiment_execution_allowed

_SECTION = re.compile(r"^##\s+7\.", re.MULTILINE)
_NEXT_SECTION = re.compile(r"^##\s+", re.MULTILINE)
_TOP_ITEM = re.compile(r"^(\d+)\.\s+(.*)$")


def extract_synthesis_next_steps(text: str) -> list[str]:
    """
    Extract the numbered items from SYNTHESIS section 7.

    :param text: SYNTHESIS.md content.
    :return: Top-level numbered items (empty when the section is absent).
    """
    start = _SECTION.search(text)
    if start is None:
        return []
    remainder = text[start.end() :]
    end = _NEXT_SECTION.search(remainder)
    section = remainder[: end.start()] if end else remainder
    steps: list[str] = []
    current: str | None = None
    for raw in section.splitlines():
        stripped = raw.strip()
        match = _TOP_ITEM.match(stripped)
        if match:
            if current is not None:
                steps.append(current.strip())
            current = match.group(2).strip()
            continue
        if current is None:
            continue
        if not stripped or stripped.startswith(("-", "*")):
            steps.append(current.strip())
            current = None
            continue
        current = f"{current} {stripped}"
    if current is not None:
        steps.append(current.strip())
    return steps


@dataclass
class NextTaskResult:
    """Outcome of the next-task proposal step."""

    path: Path
    written: bool
    reason: str
    content: str
    executed: bool = False


def _render(gate: PhaseGate, run_id: str, steps: list[str], source: Path) -> str:
    """
    Render the proposal document.

    :param gate: Phase gate snapshot.
    :param run_id: Stable run identifier.
    :param steps: Extracted next-step candidates.
    :param source: SYNTHESIS path used.
    :return: Markdown proposal.
    """
    lines = [
        "# NEXT TASK — PROPOSAL ONLY (NOT EXECUTED)",
        "",
        f"**Run ID:** `{run_id}`  ",
        "**Status:** PROPOSAL ONLY. The bridge did not execute, start or authorise "
        "this task; a human must decide and act.  ",
        f"**Gate:** phase={gate.phase}, allow_new_experiments={gate.allow_new_experiments}, "
        f"stop_after_phase_completion={gate.stop_after_phase_completion}  ",
        "",
        "## Recommended next steps",
        "",
    ]
    if steps:
        for index, step in enumerate(steps, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append(
            "No structured next steps were found in `.mece/SYNTHESIS.md`; "
            "review that document (and `research/decisions/DECISION_LOG.md`) manually."
        )
    lines += [
        "",
        "## Guardrails",
        "",
        "- This is a proposal, not an execution. Nothing has been run.",
        "- No new experiment may be executed while the phase gate is closed.",
        "- The frozen production strategy subtrees must remain untouched.",
        "- A human must record any decision in `research/decisions/DECISION_LOG.md` first.",
        "",
        "## Sources",
        "",
        f"- `{source}`",
        "- `research/decisions/DECISION_LOG.md`",
        "- `docs/EXPERIMENT_REGISTRY.md`",
        "",
    ]
    return "\n".join(lines)


def propose_next_task(
    cfg: BridgeConfig,
    gate: PhaseGate,
    run_id: str,
    *,
    force: bool = False,
) -> NextTaskResult:
    """
    Write the next-task proposal without executing anything.

    :param cfg: Bridge configuration.
    :param gate: Phase gate snapshot.
    :param run_id: Stable run identifier.
    :param force: Overwrite an existing proposal.
    :return: Proposal result (``executed`` is always False).
    :raises ValueError: When ``run_id`` is unsafe.
    """
    run_id = sanitize_run_id(run_id)
    source = cfg.root / SYNTHESIS_FILE.relative_to(PROJECT_ROOT)
    steps = (
        extract_synthesis_next_steps(source.read_text(encoding="utf-8")) if source.is_file() else []
    )
    content = _render(gate, run_id, steps, source)
    path = cfg.root / NEXT_TASK_FILE.relative_to(PROJECT_ROOT)
    if path.exists() and not force:
        return NextTaskResult(
            path=path,
            written=False,
            reason="proposal already exists (use --force to overwrite)",
            content=content,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    allowed = experiment_execution_allowed(gate)
    return NextTaskResult(
        path=path,
        written=True,
        reason="written" if allowed else "written (execution still blocked by gate)",
        content=content,
    )
