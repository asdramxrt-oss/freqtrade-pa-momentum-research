"""Non-interactive OpenCode CLI client.

This is the only place the bridge talks to OpenCode. It never runs a shell, it
never auto-approves permissions, and it never runs recursively without an
explicit opt-in from the operator. A transcript is always written under
``.mece/logs/`` so the exact prompt and output are auditable.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from automation.config import BridgeConfig, ensure_dir, sanitize_run_id, utc_stamp

ProcessRunner = Callable[..., "subprocess.CompletedProcess[str]"]


@dataclass
class OpenCodeResult:
    """Outcome of one OpenCode invocation."""

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
        """Return True when OpenCode ran and produced output."""
        if self.skipped:
            return True
        if self.timed_out or self.returncode != 0:
            return False
        return bool(self.stdout_tail.strip())


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


def _wrap_script(binary: str) -> list[str]:
    """
    Wrap a PowerShell script so it can be launched by ``subprocess``.

    :param binary: Resolved OpenCode binary/script path.
    :return: Base argv prefix.
    """
    if binary.lower().endswith(".ps1"):
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", binary]
    return [binary]


def build_command(
    binary: str,
    prompt: str,
    model: str | None = None,
    agent: str | None = None,
    directory: Path | str | None = None,
) -> tuple[str, ...]:
    """
    Build the non-interactive OpenCode argv.

    :param binary: Resolved OpenCode binary/script.
    :param prompt: Message to send.
    :param model: Optional ``provider/model``.
    :param agent: Optional agent name.
    :param directory: Optional working directory.
    :return: Full argv tuple.
    :raises ValueError: When the prompt is empty.
    """
    if not prompt or not prompt.strip():
        raise ValueError("opencode prompt must be non-empty")
    argv = [*_wrap_script(binary), "run"]
    if model:
        argv += ["--model", model]
    if agent:
        argv += ["--agent", agent]
    if directory:
        argv += ["--dir", str(directory)]
    argv.append(prompt)
    return tuple(argv)


def run_opencode(
    cfg: BridgeConfig,
    prompt: str,
    *,
    name: str = "opencode",
    timeout_s: float | None = None,
    logs_dir: Path | None = None,
    runner: ProcessRunner | None = None,
) -> OpenCodeResult:
    """
    Run OpenCode non-interactively and record a transcript.

    :param cfg: Bridge configuration.
    :param prompt: Message to send.
    :param name: Transcript label.
    :param timeout_s: Timeout override.
    :param logs_dir: Transcript directory override.
    :param runner: Injectable process runner.
    :return: Invocation result.
    :raises ValueError: When ``name`` is unsafe for a transcript filename.
    """
    name = sanitize_run_id(name)
    if cfg.opencode is None:
        return OpenCodeResult(
            argv=(),
            returncode=None,
            timed_out=False,
            skipped=True,
            skipped_reason=f"opencode unavailable ({cfg.opencode_source})",
            log_path=None,
            stdout_tail="",
            stderr_tail="",
        )
    argv = build_command(
        cfg.opencode,
        prompt,
        model=cfg.opencode_model,
        agent=cfg.opencode_agent,
        directory=cfg.root,
    )
    run = runner or _default_run
    directory = ensure_dir(logs_dir or cfg.logs_dir)
    log_path = directory / f"{utc_stamp()}_opencode_{name}.log"
    env = os.environ.copy()
    timed_out = False
    try:
        completed = run(list(argv), cfg.root, env, timeout_s or cfg.timeout_s)
        returncode = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired:
        timed_out = True
        returncode = None
        stdout = ""
        stderr = f"timeout after {timeout_s or cfg.timeout_s}s"
    log_path.write_text(
        "$ " + " ".join(argv) + "\n\n" + stdout + "\n" + stderr,
        encoding="utf-8",
    )
    return OpenCodeResult(
        argv=argv,
        returncode=returncode,
        timed_out=timed_out,
        skipped=False,
        skipped_reason="",
        log_path=log_path,
        stdout_tail="\n".join(stdout.splitlines()[-40:]),
        stderr_tail="\n".join(stderr.splitlines()[-20:]),
    )


def probe_capability(
    cfg: BridgeConfig,
    runner: ProcessRunner | None = None,
) -> tuple[bool, str]:
    """
    Verify the OpenCode non-interactive ``run`` subcommand exists.

    :param cfg: Bridge configuration.
    :param runner: Injectable process runner.
    :return: ``(available, detail)``.
    """
    if cfg.opencode is None:
        return False, f"opencode unavailable ({cfg.opencode_source})"
    argv = [*_wrap_script(cfg.opencode), "--help"]
    run = runner or _default_run
    try:
        completed = run(list(argv), cfg.root, os.environ.copy(), cfg.timeout_s)
    except subprocess.TimeoutExpired:
        return False, "opencode --help timed out"
    text = f"{completed.stdout or ''}\n{completed.stderr or ''}"
    if completed.returncode != 0:
        return False, f"opencode --help failed (exit {completed.returncode})"
    if "\n  opencode run" not in f"\n{text}" and "opencode run" not in text:
        return False, "opencode 'run' subcommand not found in help output"
    return True, "opencode run available"
