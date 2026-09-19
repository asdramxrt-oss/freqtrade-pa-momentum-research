"""Configuration and path resolution for the Phase-2 automation bridge.

The bridge is *orchestration only*: it shells out to the existing research
runners and never re-implements strategy or metric logic. Everything it needs
to locate is resolved here, explicitly, so the bridge never depends on whatever
``python`` happens to be first on ``PATH`` (on this machine the bare ``python``
can be an unrelated CrewAI virtualenv that lacks pandas/ruff).
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MECE_DIR = PROJECT_ROOT / ".mece"
LOGS_DIR = MECE_DIR / "logs"
CELLS_DIR = MECE_DIR / "cells"
GATE_FILE = MECE_DIR / "PHASE_GATE.json"
WAVE_FILE = MECE_DIR / "WAVE.md"
SYNTHESIS_FILE = MECE_DIR / "SYNTHESIS.md"
NEXT_TASK_FILE = MECE_DIR / "NEXT_TASK.md"

REPORTS_DIR = PROJECT_ROOT / "reports"
RESULTS_DIR = PROJECT_ROOT / "research" / "experiment_results"
USER_DATA_DIR = PROJECT_ROOT / "user_data"
SCRIPTS_DIR = USER_DATA_DIR / "scripts"
DIAGNOSTICS_DIR = SCRIPTS_DIR / "diagnostics"

# Frozen production strategy subtrees. The bridge must never change these.
PRODUCTION_SUBTREES = (
    "user_data/strategies/turtle",
    "user_data/strategies/pullback",
    "user_data/strategies/shared",
)

# Tracked analysis artifacts whose bytes must not change during a bridge run.
TRACKED_RESULT_GLOBS = (
    "research/experiment_results/*.json",
    "research/experiment_results/*.md",
)

DEFAULT_TIMEOUT_S = 600.0


def _npm_global() -> Path | None:
    """
    Return the global npm directory on Windows, if it can be determined.

    :return: ``%APPDATA%/npm`` when ``APPDATA`` is set, else ``None``.
    """
    appdata = os.environ.get("APPDATA")
    return Path(appdata) / "npm" if appdata else None


@dataclass(frozen=True)
class BridgeConfig:
    """Resolved, immutable bridge configuration."""

    root: Path
    python: str
    python_source: str
    opencode: str | None
    opencode_source: str
    opencode_model: str | None
    opencode_agent: str | None
    timeout_s: float

    @property
    def logs_dir(self) -> Path:
        """Return the bridge log directory (``.mece/logs``)."""
        return self.root / ".mece" / "logs"

    @property
    def reports_dir(self) -> Path:
        """Return the reports directory (``reports``)."""
        return self.root / "reports"

    @property
    def results_dir(self) -> Path:
        """Return the recorded-results directory."""
        return self.root / "research" / "experiment_results"


def utc_stamp() -> str:
    """
    Return a compact UTC timestamp matching the existing ``.mece/logs`` names.

    :return: Timestamp such as ``20260918T121908Z``.
    """
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


_RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def sanitize_run_id(run_id: str) -> str:
    """
    Validate a run identifier before it is used in a filesystem path.

    Rejects anything that is not ``[A-Za-z0-9._-]`` (so no path separators or
    traversal), plus the bare ``.`` and ``..`` names. This prevents a run id
    such as ``..\\..\\x`` from escaping ``reports/`` or ``.mece/logs/``.

    :param run_id: Candidate run identifier.
    :return: The identifier unchanged when valid.
    :raises ValueError: When the identifier is unsafe.
    """
    if not isinstance(run_id, str) or not _RUN_ID_RE.match(run_id):
        raise ValueError(f"invalid run_id {run_id!r}: must match [A-Za-z0-9._-]{{1,128}}")
    if run_id in (".", ".."):
        raise ValueError(f"invalid run_id {run_id!r}: must not be a dot path segment")
    return run_id


def resolve_python() -> tuple[str, str]:
    """
    Resolve the interpreter used for local analysis subprocesses.

    :return: ``(path, source_label)``.
    :raises FileNotFoundError: When ``PA_BRIDGE_PYTHON`` points at nothing.
    """
    env = os.environ.get("PA_BRIDGE_PYTHON")
    if env:
        candidate = Path(env)
        if candidate.is_file():
            return str(candidate), "PA_BRIDGE_PYTHON"
        raise FileNotFoundError(f"PA_BRIDGE_PYTHON is set but not a file: {env}")
    return sys.executable, "sys.executable"


def resolve_opencode() -> tuple[str | None, str]:
    """
    Locate the OpenCode CLI without executing it.

    :return: ``(path_or_none, source_label)``.
    """
    env = os.environ.get("OPENCODE_BIN")
    if env:
        if Path(env).is_file() or shutil.which(env):
            return env, "OPENCODE_BIN"
        return None, f"OPENCODE_BIN set but not found: {env}"

    for name in ("opencode", "opencode.exe", "opencode.cmd"):
        found = shutil.which(name)
        if found:
            return found, f"which({name})"

    npm = _npm_global()
    if npm is not None:
        candidates = (
            npm / "node_modules" / "opencode-ai" / "bin" / "opencode.exe",
            npm / "opencode.cmd",
            npm / "opencode.exe",
            npm / "opencode.ps1",
        )
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate), f"npm:{candidate.name}"

    return None, "not found on PATH or npm global"


def load_config(root: Path | str = PROJECT_ROOT) -> BridgeConfig:
    """
    Build the resolved bridge configuration.

    :param root: Repository root (overridable for tests).
    :return: Populated :class:`BridgeConfig`.
    """
    python, python_source = resolve_python()
    opencode, opencode_source = resolve_opencode()
    try:
        timeout = float(os.environ.get("PA_BRIDGE_TIMEOUT_S", DEFAULT_TIMEOUT_S))
    except ValueError:
        timeout = DEFAULT_TIMEOUT_S
    return BridgeConfig(
        root=Path(root).resolve(),
        python=python,
        python_source=python_source,
        opencode=opencode,
        opencode_source=opencode_source,
        opencode_model=os.environ.get("OPENCODE_MODEL") or None,
        opencode_agent=os.environ.get("OPENCODE_AGENT") or None,
        timeout_s=timeout,
    )


def ensure_dir(path: Path) -> Path:
    """
    Create a directory (and parents) if missing and return it.

    :param path: Directory to create.
    :return: The same path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
