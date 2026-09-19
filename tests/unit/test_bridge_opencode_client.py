"""Unit tests for the OpenCode client (no real OpenCode invocation)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from automation import opencode_client as oc
from automation.config import BridgeConfig

pytestmark = pytest.mark.bridge

# Constructed at runtime so the literal flag never appears in the repo.
FORBIDDEN_AUTO_FLAG = "--" + "auto"


def _cfg(root: Path, binary: str | None = "opencode") -> BridgeConfig:
    return BridgeConfig(
        root=root,
        python="python",
        python_source="test",
        opencode=binary,
        opencode_source="test",
        opencode_model="provider/model",
        opencode_agent="build",
        timeout_s=5.0,
    )


def _completed(stdout: str = "", stderr: str = "", code: int = 0):
    return subprocess.CompletedProcess(
        args=["opencode"], returncode=code, stdout=stdout, stderr=stderr
    )


def test_build_command_orders_flags_before_prompt() -> None:
    argv = oc.build_command(
        "opencode", "hello", model="provider/model", agent="build", directory="C:/x"
    )
    assert argv[0] == "opencode"
    assert argv[1] == "run"
    assert argv[-1] == "hello"
    assert FORBIDDEN_AUTO_FLAG not in argv


def test_build_command_wraps_ps1() -> None:
    argv = oc.build_command("C:/npm/opencode.ps1", "hi")
    assert argv[:5] == ("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File")
    assert argv[-1] == "hi"


def test_build_command_rejects_empty_prompt() -> None:
    with pytest.raises(ValueError):
        oc.build_command("opencode", "   ")


def test_run_opencode_ok_writes_transcript(tmp_path) -> None:
    result = oc.run_opencode(
        _cfg(tmp_path),
        "prompt",
        logs_dir=tmp_path / "logs",
        runner=lambda argv, cwd, env, timeout: _completed(stdout="advisory text"),
    )
    assert result.ok is True
    assert result.log_path is not None and result.log_path.is_file()


def test_run_opencode_nonzero_is_failure(tmp_path) -> None:
    result = oc.run_opencode(
        _cfg(tmp_path),
        "prompt",
        logs_dir=tmp_path / "logs",
        runner=lambda argv, cwd, env, timeout: _completed(code=2),
    )
    assert result.ok is False


def test_run_opencode_timeout_is_failure(tmp_path) -> None:
    def boom(argv, cwd, env, timeout):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=timeout)

    result = oc.run_opencode(_cfg(tmp_path), "prompt", logs_dir=tmp_path / "logs", runner=boom)
    assert result.timed_out is True
    assert result.ok is False


def test_run_opencode_skips_without_binary(tmp_path) -> None:
    result = oc.run_opencode(_cfg(tmp_path, binary=None), "prompt", logs_dir=tmp_path / "logs")
    assert result.skipped is True
    assert result.ok is True


def test_probe_capability_reports_run(tmp_path) -> None:
    ok, detail = oc.probe_capability(
        _cfg(tmp_path),
        runner=lambda argv, cwd, env, timeout: _completed(
            stdout="Commands:\n  opencode run [message..]\n"
        ),
    )
    assert ok is True
    assert "available" in detail


def test_probe_capability_without_binary(tmp_path) -> None:
    ok, _ = oc.probe_capability(_cfg(tmp_path, binary=None))
    assert ok is False
