"""Deterministic REPORT.md generator.

The report is a **derived view** over the committed research artifacts, exactly
as ``reports/README.md`` requires: it is regenerable from the recorded JSON
without re-running any backtest. It contains no wall-clock timestamps, so
identical inputs always produce byte-identical output.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from automation.config import PROJECT_ROOT, BridgeConfig, sanitize_run_id
from automation.gate import PhaseGate
from automation.validation import ARTIFACT_IDS, Check


def _read_json(path: Path) -> dict | None:
    """
    Read a JSON object or return None.

    :param path: File path.
    :return: Parsed mapping, or None.
    """
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _first_sentence(text: object) -> str:
    """
    Return the first sentence of a decision string.

    :param text: Arbitrary value.
    :return: Deterministic single-line excerpt.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    sentence = text.strip().split(". ", 1)[0].strip()
    if not sentence.endswith("."):
        sentence += "."
    return sentence.replace("\n", " ")


def input_digest(root: Path | str = PROJECT_ROOT) -> str:
    """
    SHA-256 digest over the committed artifact files.

    :param root: Repository root.
    :return: Hex digest.
    """
    base = Path(root) / "research" / "experiment_results"
    digest = hashlib.sha256()
    for exp_id in ARTIFACT_IDS:
        for suffix in (".json", ".md"):
            path = base / f"{exp_id}{suffix}"
            digest.update(f"{exp_id}{suffix}".encode())
            digest.update(path.read_bytes() if path.is_file() else b"<missing>")
    return digest.hexdigest()


@dataclass(frozen=True)
class ArtifactRow:
    """One artifact row in the report."""

    experiment_id: str
    status: str
    verdict: str
    production_changed: str
    funding_applied: str
    decision: str


def artifact_rows(root: Path | str = PROJECT_ROOT) -> list[ArtifactRow]:
    """
    Build deterministic report rows from the committed artifacts.

    :param root: Repository root.
    :return: Rows, one per known artifact.
    """
    base = Path(root) / "research" / "experiment_results"
    rows: list[ArtifactRow] = []
    for exp_id in ARTIFACT_IDS:
        data = _read_json(base / f"{exp_id}.json")
        if data is None:
            rows.append(ArtifactRow(exp_id, "MISSING", "MISSING", "?", "?", "Artifact not found."))
            continue
        changed = data.get("production_strategy_changed")
        funding = data.get("funding_applied")
        rows.append(
            ArtifactRow(
                experiment_id=str(data.get("experiment_id", exp_id)),
                status=str(data.get("status", "UNKNOWN")),
                verdict=str(data.get("verdict", "UNKNOWN")),
                production_changed="no" if changed is False else str(changed),
                funding_applied="yes" if funding is True else str(funding),
                decision=_first_sentence(data.get("decision")),
            )
        )
    return rows


def render_report(
    root: Path | str,
    run_id: str,
    gate: PhaseGate,
    validation: Iterable[Check] = (),
    next_task_path: Path | None = None,
) -> str:
    """
    Render the deterministic REPORT.md content.

    :param root: Repository root.
    :param run_id: Stable run identifier supplied by the caller.
    :param gate: Phase gate snapshot.
    :param validation: Validation checks to record.
    :param next_task_path: Where the next-task proposal was written.
    :return: Markdown report.
    :raises ValueError: When ``run_id`` is unsafe.
    """
    run_id = sanitize_run_id(run_id)
    lines: list[str] = [
        "# Phase-2 Automation Bridge — REPORT",
        "",
        f"**Run ID:** `{run_id}`  ",
        "**Generator:** `automation.report` (deterministic, derived view)  ",
        "**Source of truth:** `research/experiment_results/`  ",
        "",
        "> This report is a derived view. If it disagrees with a recorded result, "
        "the recorded result wins.",
        "",
        "## Governance",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Phase | {gate.phase} |",
        f"| Allow new experiments | {gate.allow_new_experiments} |",
        f"| Stop after phase completion | {gate.stop_after_phase_completion} |",
        "",
        "## Artifacts",
        "",
        "| Experiment | Status | Verdict | Production changed | Funding applied |",
        "|------------|--------|---------|--------------------|-----------------|",
    ]
    for row in artifact_rows(root):
        lines.append(
            f"| {row.experiment_id} | {row.status} | {row.verdict} | "
            f"{row.production_changed} | {row.funding_applied} |"
        )
    lines += ["", "### Decisions", ""]
    for row in artifact_rows(root):
        lines.append(f"- **{row.experiment_id}:** {row.decision}")
    lines += ["", "## Validation", ""]
    checks = list(validation)
    if checks:
        lines += ["| Check | Result | Detail |", "|-------|--------|--------|"]
        for check in checks:
            lines.append(f"| {check.name} | {'PASS' if check.ok else 'FAIL'} | {check.detail} |")
    else:
        lines.append("_No validation checks supplied._")
    lines += [
        "",
        "## Integrity",
        "",
        f"- Input digest (sha256): `{input_digest(root)}`",
        "- Production strategy subtrees: asserted untouched by `automation.validation`.",
        "- Research-only: no live-trading code path exists in this bridge.",
        "",
        "## Next step",
        "",
    ]
    if next_task_path is not None:
        lines.append(f"- Proposal written to: `{next_task_path}` (PROPOSAL ONLY — not executed).")
    else:
        lines.append("- No next-task proposal was produced in this run.")
    lines += [
        "",
        "## Notices",
        "",
        "- The bridge never executes the next task; a human decides.",
        "- No experiment is started while the phase gate forbids it.",
        "",
    ]
    return "\n".join(lines)


def write_report(root: Path | str, run_id: str, content: str) -> Path:
    """
    Write the report to ``reports/<run_id>_REPORT.md``.

    :param root: Repository root.
    :param run_id: Stable run identifier.
    :param content: Rendered markdown.
    :return: Written path.
    :raises ValueError: When ``run_id`` is unsafe.
    """
    run_id = sanitize_run_id(run_id)
    directory = Path(root) / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run_id}_REPORT.md"
    path.write_text(content, encoding="utf-8")
    return path


def build_report(
    cfg: BridgeConfig,
    gate: PhaseGate,
    run_id: str,
    validation: Iterable[Check] = (),
    next_task_path: Path | None = None,
) -> Path:
    """
    Render and write the report in one call.

    :param cfg: Bridge configuration.
    :param gate: Phase gate snapshot.
    :param run_id: Stable run identifier.
    :param validation: Validation checks.
    :param next_task_path: Next-task proposal path.
    :return: Written report path.
    """
    content = render_report(cfg.root, run_id, gate, validation, next_task_path)
    return write_report(cfg.root, run_id, content)
