"""Unit tests for the local analysis runner wrappers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from automation import runners
from automation.config import BridgeConfig
from automation.gate import PhaseGate

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
        timeout_s=5.0,
    )


def _gate(allow: bool, stop: bool) -> PhaseGate:
    return PhaseGate(
        phase="PHASE2",
        allow_new_experiments=allow,
        stop_after_phase_completion=stop,
        path=Path("g.json"),
        raw={},
    )


def _ok_runner(argv, cwd, env, timeout):
    return subprocess.CompletedProcess(args=argv, returncode=0, stdout="ok", stderr="")


def test_build_diagnostic_commands(tmp_path) -> None:
    commands = runners.build_diagnostic_commands(_cfg(tmp_path))
    assert len(commands) == len(runners.DIAGNOSTIC_SCRIPTS)
    assert all(command.kind == "diagnostic" for command in commands)
    assert all(command.argv[0] == "python" for command in commands)


def test_experiments_refused_when_gate_closed(tmp_path) -> None:
    with pytest.raises(PermissionError):
        runners.run_analysis(
            _cfg(tmp_path),
            _gate(False, True),
            include_experiments=True,
        )


def test_experiments_allowed_when_gate_open(tmp_path) -> None:
    results = runners.run_analysis(
        _cfg(tmp_path),
        _gate(True, False),
        include_experiments=True,
        only=["p3_exp003_carry"],
        runner=_ok_runner,
    )
    assert len(results) == 1
    assert results[0].ok is True


def test_run_command_records_failure(tmp_path) -> None:
    def failing(argv, cwd, env, timeout):
        return subprocess.CompletedProcess(args=argv, returncode=1, stdout="", stderr="boom")

    command = runners.build_diagnostic_commands(_cfg(tmp_path))[0]
    result = runners.run_command(
        command, _cfg(tmp_path), logs_dir=tmp_path / "logs", runner=failing
    )
    assert result.ok is False
    assert result.log_path is not None and result.log_path.is_file()


def test_run_analysis_without_only_or_flags_returns_empty(tmp_path) -> None:
    with pytest.raises(ValueError):
        runners.run_analysis(_cfg(tmp_path), _gate(False, True), only=["nonexistent"])
