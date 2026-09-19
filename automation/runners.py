"""Thin wrappers around the existing local Python/Freqtrade analysis runners.

The bridge re-implements nothing. It locates the committed runner scripts,
executes them with an explicit interpreter and records a transcript. Experiment
execution is refused unless the phase gate explicitly authorises it.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from automation.config import BridgeConfig, ensure_dir, utc_stamp
from automation.gate import PhaseGate, experiment_execution_allowed

DIAGNOSTIC_SCRIPTS = (
    "diagnose_data_quality.py",
    "diagnose_market_regimes.py",
    "diagnose_turtle_followthrough.py",
    "diagnose_pullback_geometry.py",
    "diagnose_trades.py",
    "diagnose_statistics.py",
)

EXPERIMENT_SCRIPTS = (
    "p3_exp001_run.py",
    "p3_exp002_costs.py",
    "p3_exp003_carry.py",
)

ProcessRunner = Callable[..., "subprocess.CompletedProcess[str]"]


@dataclass(frozen=True)
class AnalysisCommand:
    """A single local analysis command."""

    name: str
    argv: tuple[str, ...]
    kind: str  # "diagnostic" | "experiment"


@dataclass
class CommandResult:
    """Outcome of one analysis command."""

    name: str
    kind: str
    argv: tuple[str, ...]
    returncode: int | None
    timed_out: bool
    skipped: bool
    skipped_reason: str
    log_path: Path | None
    stdout_tail: str
    stderr_tail: str

    @property
    def ok(self) -> bool:
        """Return True when the command succeeded (or was intentionally skipped)."""
        if self.skipped:
            return True
        return self.returncode == 0 and not self.timed_out


def _default_run(
    argv: Sequence[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Execute a command with capture, never through a shell.

    :param argv: Full argv list.
    :param cwd: Working directory.
    :param env: Environment override.
    :param timeout: Timeout in seconds.
    :return: Completed process.
    """
    return subprocess.run(
        list(argv),
        cwd=str(cwd),
        env=env,
        timeout=timeout,
        capture_output=True,
        text=True,
        check=False,
    )


def build_diagnostic_commands(cfg: BridgeConfig) -> list[AnalysisCommand]:
    """
    Build the read-only Phase-2 diagnostic commands.

    :param cfg: Bridge configuration.
    :return: List of diagnostic commands.
    """
    directory = cfg.root / "user_data" / "scripts" / "diagnostics"
    return [
        AnalysisCommand(
            name=Path(script).stem,
            argv=(cfg.python, str(directory / script)),
            kind="diagnostic",
        )
        for script in DIAGNOSTIC_SCRIPTS
    ]


def build_experiment_commands(cfg: BridgeConfig) -> list[AnalysisCommand]:
    """
    Build the experiment-class commands (require gate authorisation).

    :param cfg: Bridge configuration.
    :return: List of experiment commands.
    """
    directory = cfg.root / "user_data" / "scripts"
    return [
        AnalysisCommand(
            name=Path(script).stem,
            argv=(cfg.python, str(directory / script)),
            kind="experiment",
        )
        for script in EXPERIMENT_SCRIPTS
    ]


def run_command(
    command: AnalysisCommand,
    cfg: BridgeConfig,
    logs_dir: Path | None = None,
    runner: ProcessRunner | None = None,
) -> CommandResult:
    """
    Execute one analysis command and write its transcript.

    :param command: Command descriptor.
    :param cfg: Bridge configuration.
    :param logs_dir: Directory for transcripts (defaults to ``.mece/logs``).
    :param runner: Injectable process runner.
    :return: Command result.
    """
    run = runner or _default_run
    directory = ensure_dir(logs_dir or cfg.logs_dir)
    log_path = directory / f"{utc_stamp()}_analysis_{command.name}.log"
    env = os.environ.copy()
    timed_out = False
    try:
        completed = run(list(command.argv), cfg.root, env, cfg.timeout_s)
        returncode = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout or "" if isinstance(exc.stdout, str) else ""
        stderr = f"timeout after {cfg.timeout_s}s"
    log_path.write_text(
        "$ " + " ".join(command.argv) + "\n\n" + stdout + "\n" + stderr,
        encoding="utf-8",
    )
    return CommandResult(
        name=command.name,
        kind=command.kind,
        argv=command.argv,
        returncode=returncode,
        timed_out=timed_out,
        skipped=False,
        skipped_reason="",
        log_path=log_path,
        stdout_tail="\n".join(stdout.splitlines()[-20:]),
        stderr_tail="\n".join(stderr.splitlines()[-20:]),
    )


def run_analysis(
    cfg: BridgeConfig,
    gate: PhaseGate,
    *,
    include_experiments: bool = False,
    only: Sequence[str] | None = None,
    logs_dir: Path | None = None,
    runner: ProcessRunner | None = None,
) -> list[CommandResult]:
    """
    Run the analysis step.

    Diagnostics are always permitted. Experiment runners are included only when
    requested *and* the gate authorises execution; otherwise a
    :class:`PermissionError` is raised (never silently downgraded).

    :param cfg: Bridge configuration.
    :param gate: Phase gate snapshot.
    :param include_experiments: Include the experiment-class runners.
    :param only: Restrict to these command names.
    :param logs_dir: Transcript directory override.
    :param runner: Injectable process runner.
    :return: Command results.
    :raises PermissionError: When experiment execution is not authorised.
    """
    commands = build_diagnostic_commands(cfg)
    if include_experiments:
        if not experiment_execution_allowed(gate):
            raise PermissionError(
                "phase gate forbids new experiment execution "
                f"(phase={gate.phase}, allow_new_experiments={gate.allow_new_experiments}, "
                f"stop_after_phase_completion={gate.stop_after_phase_completion})"
            )
        commands.extend(build_experiment_commands(cfg))
    if only:
        wanted = set(only)
        commands = [command for command in commands if command.name in wanted]
    if not commands:
        raise ValueError("no analysis commands selected")
    return [run_command(command, cfg, logs_dir, runner) for command in commands]
