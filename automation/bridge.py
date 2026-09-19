"""One-click automation bridge CLI.

Chain (per the approved plan):

    gate -> analysis -> opencode -> validation -> REPORT.md -> next-task

All steps are read-only with respect to the frozen production subtrees and the
recorded experiment results. External or heavy steps (real analysis, OpenCode)
are opt-in. The next task is always a proposal, never an execution.

Usage::

    python -m automation.bridge --dry-run
    python -m automation.bridge --json
    python -m automation.bridge --run-analysis
    python -m automation.bridge --with-opencode
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from automation import crew as crew_mod
from automation import next_task as next_task_mod
from automation import opencode_client, runners, validation
from automation import report as report_mod
from automation.config import (
    DEFAULT_TIMEOUT_S,
    PROJECT_ROOT,
    BridgeConfig,
    load_config,
    sanitize_run_id,
)
from automation.gate import GateError, PhaseGate, experiment_execution_allowed, load_gate

DEFAULT_RUN_ID = "phase2_bridge"
DEFAULT_OPENCODE_PROMPT = (
    "Read-only advisory review of the Phase-2 research state. Do not modify, "
    "create or delete files; do not run experiments; do not commit. Summarise "
    "the phase gate, validation status, and the recommended next step from "
    ".mece/SYNTHESIS.md section 7. Output text only."
)

EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_VALIDATION = 2
EXIT_OPENCODE = 3
EXIT_ANALYSIS = 4
EXIT_CREW = 5

STEPS = (
    "all",
    "crew",
    "gate",
    "analysis",
    "opencode",
    "validation",
    "report",
    "next-task",
)


def _selected(step: str, name: str) -> bool:
    """
    Report whether a step should run.

    :param step: Requested step.
    :param name: Candidate step name.
    :return: True when selected.
    """
    return step in ("all", name)


def _parser() -> argparse.ArgumentParser:
    """
    Build the CLI parser.

    :return: Argument parser.
    """
    parser = argparse.ArgumentParser(prog="automation.bridge", description=__doc__)
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="repository root")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="stable run identifier")
    parser.add_argument("--step", choices=STEPS, default="all", help="run a single step")
    parser.add_argument(
        "--with-crew",
        action="store_true",
        help="run the CrewAI orchestration stage (opt-in; needs the 'bridge' extra)",
    )
    parser.add_argument(
        "--run-analysis",
        action="store_true",
        help="execute the local diagnostic scripts (opt-in; may rewrite tracked JSON)",
    )
    parser.add_argument(
        "--include-experiments",
        action="store_true",
        help="also execute experiment-class runners (requires an open gate)",
    )
    parser.add_argument(
        "--with-opencode",
        action="store_true",
        help="invoke OpenCode non-interactively (opt-in)",
    )
    parser.add_argument("--opencode-prompt", default=DEFAULT_OPENCODE_PROMPT)
    parser.add_argument("--force", action="store_true", help="overwrite the next-task proposal")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and write nothing")
    parser.add_argument("--json", action="store_true", help="emit the summary as JSON")
    return parser


def _emit(summary: dict[str, Any], as_json: bool) -> None:
    """
    Print the run summary.

    :param summary: Summary dictionary.
    :param as_json: Emit JSON instead of text.
    """
    if as_json:
        print(json.dumps(summary, indent=2, default=str))
        return
    print(f"Bridge run id: {summary['run_id']}")
    print(f"Root         : {summary['root']}")
    print(f"Dry run      : {summary['dry_run']}")
    if summary.get("gate"):
        gate = summary["gate"]
        print(
            f"Gate         : phase={gate['phase']} "
            f"allow_new_experiments={gate['allow_new_experiments']} "
            f"stop_after_phase_completion={gate['stop_after_phase_completion']}"
        )
    for name, step in summary["steps"].items():
        print(f"  [{name}] {step.get('status', 'done')}: {step.get('detail', '')}".rstrip())


def _plan_summary(cfg: BridgeConfig, gate: PhaseGate, args: argparse.Namespace) -> dict[str, Any]:
    """
    Build a no-side-effect dry-run summary.

    :param cfg: Bridge configuration.
    :param gate: Phase gate snapshot.
    :param args: Parsed arguments.
    :return: Summary dictionary.
    """
    planned: list[str] = []
    if args.with_crew:
        planned.append("crew")
    if args.run_analysis:
        planned.append("analysis")
    if args.with_opencode:
        planned.append("opencode")
    planned += ["validation", "report", "next-task"]
    return {
        "run_id": args.run_id,
        "root": str(cfg.root),
        "dry_run": True,
        "python": cfg.python,
        "python_source": cfg.python_source,
        "opencode": cfg.opencode,
        "opencode_source": cfg.opencode_source,
        "gate": gate.as_dict(),
        "experiment_execution_allowed": experiment_execution_allowed(gate),
        "planned_steps": planned,
        "steps": {},
    }


def execute(args: argparse.Namespace) -> int:
    """
    Execute the bridge chain.

    :param args: Parsed arguments.
    :return: Process exit code.
    """
    root = Path(args.root).resolve()
    try:
        args.run_id = sanitize_run_id(args.run_id)
    except ValueError as exc:
        _emit(
            {
                "run_id": str(args.run_id),
                "root": str(root),
                "dry_run": args.dry_run,
                "gate": None,
                "steps": {"run-id": {"status": "error", "detail": str(exc)}},
            },
            args.json,
        )
        return EXIT_CONFIG
    try:
        cfg = load_config(root)
        gate = load_gate(cfg.root / ".mece" / "PHASE_GATE.json")
    except (GateError, FileNotFoundError) as exc:
        _emit(
            {
                "run_id": args.run_id,
                "root": str(root),
                "dry_run": args.dry_run,
                "gate": None,
                "steps": {"gate": {"status": "error", "detail": str(exc)}},
            },
            args.json,
        )
        return EXIT_CONFIG

    if args.dry_run:
        summary = _plan_summary(cfg, gate, args)
        summary["steps"] = {
            "gate": {"status": "ok", "detail": gate.phase},
            "crew": {
                "status": "planned" if args.with_crew else "skipped",
                "detail": "CrewAI orchestration" if args.with_crew else "use --with-crew",
            },
            "analysis": {
                "status": "planned" if args.run_analysis else "skipped",
                "detail": "diagnostics (read-only)" if args.run_analysis else "use --run-analysis",
            },
            "opencode": {
                "status": "planned" if args.with_opencode else "skipped",
                "detail": cfg.opencode_source,
            },
            "validation": {"status": "planned", "detail": "fail-closed"},
            "report": {"status": "planned", "detail": f"reports/{args.run_id}_REPORT.md"},
            "next-task": {"status": "planned", "detail": ".mece/NEXT_TASK.md (proposal only)"},
        }
        _emit(summary, args.json)
        return EXIT_OK

    summary: dict[str, Any] = {
        "run_id": args.run_id,
        "root": str(cfg.root),
        "dry_run": False,
        "gate": gate.as_dict(),
        "experiment_execution_allowed": experiment_execution_allowed(gate),
        "steps": {},
    }
    summary["steps"]["gate"] = {"status": "ok", "detail": gate.phase}

    # --- crew (CrewAI orchestrator) --------------------------------------
    if _selected(args.step, "crew"):
        if args.with_crew:
            try:
                crew_result = crew_mod.run_crew(cfg)
            except Exception as exc:  # noqa: BLE001 - CLI boundary must not crash
                summary["steps"]["crew"] = {"status": "error", "detail": str(exc)}
                _emit(summary, args.json)
                return EXIT_CREW
            if crew_result.skipped:
                summary["steps"]["crew"] = {
                    "status": "skipped",
                    "detail": crew_result.reason,
                }
            elif not crew_result.executed:
                summary["steps"]["crew"] = {"status": "error", "detail": crew_result.reason}
                _emit(summary, args.json)
                return EXIT_CREW
            else:
                summary["steps"]["crew"] = {"status": "ok", "detail": crew_result.reason}
        else:
            summary["steps"]["crew"] = {
                "status": "skipped",
                "detail": "use --with-crew to run the CrewAI orchestration stage",
            }

    # --- analysis ---------------------------------------------------------
    if _selected(args.step, "analysis"):
        if args.run_analysis:
            before = validation.snapshot_results(cfg.root)
            try:
                results = runners.run_analysis(
                    cfg, gate, include_experiments=args.include_experiments
                )
            except (PermissionError, ValueError) as exc:
                summary["steps"]["analysis"] = {"status": "error", "detail": str(exc)}
                _emit(summary, args.json)
                return EXIT_ANALYSIS
            after = validation.snapshot_results(cfg.root)
            unchanged, changed = validation.results_unchanged(before, after)
            failed = [result.name for result in results if not result.ok]
            detail = f"{len(results)} command(s); tracked results unchanged={unchanged}"
            if failed:
                summary["steps"]["analysis"] = {
                    "status": "error",
                    "detail": f"failed: {', '.join(failed)}",
                }
                _emit(summary, args.json)
                return EXIT_ANALYSIS
            if not unchanged:
                summary["steps"]["analysis"] = {
                    "status": "error",
                    "detail": f"analysis modified tracked results: {', '.join(changed[:5])}",
                }
                _emit(summary, args.json)
                return EXIT_ANALYSIS
            summary["steps"]["analysis"] = {"status": "ok", "detail": detail}
        else:
            summary["steps"]["analysis"] = {
                "status": "skipped",
                "detail": "use --run-analysis to execute diagnostics",
            }

    # --- opencode ---------------------------------------------------------
    if _selected(args.step, "opencode"):
        if args.with_opencode:
            before = validation.snapshot_results(cfg.root)
            result = opencode_client.run_opencode(
                cfg,
                args.opencode_prompt,
                name=f"bridge_{args.run_id}",
                timeout_s=cfg.timeout_s or DEFAULT_TIMEOUT_S,
            )
            after = validation.snapshot_results(cfg.root)
            unchanged, changed = validation.results_unchanged(before, after)
            if result.skipped:
                summary["steps"]["opencode"] = {
                    "status": "skipped",
                    "detail": result.skipped_reason,
                }
            elif not result.ok:
                summary["steps"]["opencode"] = {
                    "status": "error",
                    "detail": f"exit={result.returncode} timed_out={result.timed_out}",
                }
                _emit(summary, args.json)
                return EXIT_OPENCODE
            elif not unchanged:
                summary["steps"]["opencode"] = {
                    "status": "error",
                    "detail": f"opencode modified tracked results: {', '.join(changed[:5])}",
                }
                _emit(summary, args.json)
                return EXIT_OPENCODE
            else:
                summary["steps"]["opencode"] = {
                    "status": "ok",
                    "detail": f"log={result.log_path}",
                }
        else:
            summary["steps"]["opencode"] = {
                "status": "skipped",
                "detail": f"use --with-opencode ({cfg.opencode_source})",
            }

    # --- validation -------------------------------------------------------
    checks = []
    if _selected(args.step, "validation"):
        result = validation.run_validation(cfg.root)
        checks = result.checks
        summary["steps"]["validation"] = {
            "status": "ok" if result.ok else "error",
            "detail": "; ".join(f"{c.name}={'PASS' if c.ok else 'FAIL'}" for c in checks),
        }
        if not result.ok and args.step in ("all", "validation"):
            failures = "; ".join(f"{c.name}: {c.detail}" for c in result.failures)
            summary["steps"]["validation"] = {"status": "error", "detail": failures}
            _emit(summary, args.json)
            return EXIT_VALIDATION

    # --- report -----------------------------------------------------------
    next_task_path = cfg.root / ".mece" / "NEXT_TASK.md"
    if _selected(args.step, "report"):
        path = report_mod.build_report(
            cfg, gate, args.run_id, validation=checks, next_task_path=next_task_path
        )
        summary["steps"]["report"] = {"status": "ok", "detail": str(path)}

    # --- next task (proposal only) ---------------------------------------
    if _selected(args.step, "next-task"):
        proposal = next_task_mod.propose_next_task(cfg, gate, args.run_id, force=args.force)
        summary["steps"]["next-task"] = {
            "status": "ok" if proposal.written else "skipped",
            "detail": f"{proposal.path} ({proposal.reason}); executed={proposal.executed}",
        }

    _emit(summary, args.json)
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point.

    :param argv: Argument vector (defaults to ``sys.argv``).
    :return: Process exit code.
    """
    return execute(_parser().parse_args(argv))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
