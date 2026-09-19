"""Validation gates for the automation bridge.

Every check is fail-closed. The bridge refuses to produce a report or a
next-task proposal unless all validations pass. Four families are covered:

1. Frozen production subtrees are byte-untouched.
2. The phase gate is present and well formed.
3. Recorded analysis artifacts are present and mutually consistent.
4. The bridge's own runtime modules contain no dangerous execution patterns.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from automation.config import (
    CELLS_DIR,
    GATE_FILE,
    PRODUCTION_SUBTREES,
    PROJECT_ROOT,
    REPORTS_DIR,
    RESULTS_DIR,
    SYNTHESIS_FILE,
    TRACKED_RESULT_GLOBS,
    WAVE_FILE,
)

GitRunner = Callable[[Sequence[str], Path], "subprocess.CompletedProcess[str]"]

ARTIFACT_IDS = ("P3-EXP-001", "P3-EXP-002", "P3-EXP-003")

SAFETY_SCAN_MODULES = ("runners.py", "opencode_client.py", "bridge.py", "crew.py")
FORBIDDEN_PATTERNS = (
    "shell=True",
    "os.system(",
    "subprocess.call(",
    ".create_order(",
    ".withdraw(",
)


def _default_git_runner(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """
    Run a git command and capture output.

    :param argv: Full argv list (no shell).
    :param cwd: Working directory.
    :return: Completed process.
    """
    return subprocess.run(list(argv), cwd=str(cwd), capture_output=True, text=True, check=False)


@dataclass(frozen=True)
class Check:
    """One validation check result."""

    name: str
    ok: bool
    detail: str


@dataclass
class ValidationResult:
    """Aggregate result of all validation checks."""

    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return True only when every check passed."""
        return all(check.ok for check in self.checks)

    @property
    def failures(self) -> list[Check]:
        """Return the failed checks."""
        return [check for check in self.checks if not check.ok]

    def add(self, name: str, ok: bool, detail: str) -> None:
        """
        Append a check.

        :param name: Check name.
        :param ok: Whether it passed.
        :param detail: Human-readable detail.
        """
        self.checks.append(Check(name=name, ok=bool(ok), detail=detail))


def production_changes(
    root: Path | str = PROJECT_ROOT,
    git_runner: GitRunner | None = None,
) -> tuple[list[str], str]:
    """
    Return changes under the frozen production subtrees.

    :param root: Repository root.
    :param git_runner: Injectable git runner.
    :return: ``(changed_lines, note)``.
    """
    runner = git_runner or _default_git_runner
    argv = ["git", "-C", str(root), "status", "--porcelain", "--", *PRODUCTION_SUBTREES]
    completed = runner(argv, Path(root))
    if completed.returncode != 0 and "not a git repository" not in (completed.stderr or "").lower():
        return [], f"git status failed (exit {completed.returncode}): {completed.stderr.strip()}"
    lines = [line for line in (completed.stdout or "").splitlines() if line.strip()]
    return lines, "clean" if not lines else f"{len(lines)} change(s)"


def check_production_untouched(
    root: Path | str = PROJECT_ROOT,
    git_runner: GitRunner | None = None,
) -> Check:
    """
    Check that the frozen production strategy subtrees are untouched.

    :param root: Repository root.
    :param git_runner: Injectable git runner.
    :return: Check result.
    """
    lines, note = production_changes(root, git_runner)
    if lines:
        return Check("production_untouched", False, "; ".join(lines[:5]))
    if note.startswith("git status failed"):
        return Check("production_untouched", False, note)
    return Check("production_untouched", True, note)


def check_gate_present(root: Path | str = PROJECT_ROOT) -> Check:
    """
    Check that the phase gate exists, parses, and has boolean fields.

    :param root: Repository root.
    :return: Check result.
    """
    path = Path(root) / GATE_FILE.relative_to(PROJECT_ROOT)
    if not path.is_file():
        return Check("gate_present", False, f"missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return Check("gate_present", False, f"invalid JSON: {exc}")
    missing = [
        key
        for key in ("allow_new_experiments", "stop_after_phase_completion")
        if not isinstance(data.get(key), bool)
    ]
    if missing:
        return Check("gate_present", False, f"missing boolean(s): {', '.join(missing)}")
    return Check("gate_present", True, f"phase={data.get('phase', 'UNKNOWN')}")


def check_json_artifacts(root: Path | str = PROJECT_ROOT) -> Check:
    """
    Check recorded experiment artifacts are present and internally consistent.

    :param root: Repository root.
    :return: Check result.
    """
    results = Path(root) / RESULTS_DIR.relative_to(PROJECT_ROOT)
    problems: list[str] = []
    for exp_id in ARTIFACT_IDS:
        json_path = results / f"{exp_id}.json"
        md_path = results / f"{exp_id}.md"
        if not json_path.is_file():
            problems.append(f"{exp_id}: missing {json_path.name}")
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{exp_id}: invalid JSON ({exc})")
            continue
        if data.get("experiment_id") != exp_id:
            problems.append(f"{exp_id}: experiment_id mismatch")
        verdict = data.get("verdict")
        if not isinstance(verdict, str) or not verdict.strip():
            problems.append(f"{exp_id}: missing verdict")
            continue
        if not md_path.is_file():
            problems.append(f"{exp_id}: missing {md_path.name}")
        elif verdict not in md_path.read_text(encoding="utf-8"):
            problems.append(f"{exp_id}: verdict {verdict!r} absent from {md_path.name}")
        if "funding_applied" in data and data["funding_applied"] is not True:
            problems.append(f"{exp_id}: funding_applied is not true")
        if (
            "production_strategy_changed" in data
            and data["production_strategy_changed"] is not False
        ):
            problems.append(f"{exp_id}: production_strategy_changed is not false")
    if problems:
        return Check("json_artifacts", False, "; ".join(problems[:5]))
    return Check("json_artifacts", True, f"{len(ARTIFACT_IDS)} artifacts consistent")


def required_artifact_paths(root: Path | str = PROJECT_ROOT) -> list[Path]:
    """
    Return the artifacts that must exist for a valid bridge run.

    :param root: Repository root.
    :return: List of required paths.
    """
    base = Path(root)

    def rel(path: Path) -> Path:
        return base / path.relative_to(PROJECT_ROOT)

    paths = [
        rel(GATE_FILE),
        rel(WAVE_FILE),
        rel(SYNTHESIS_FILE),
        rel(REPORTS_DIR / "README.md"),
    ]
    paths.extend(rel(CELLS_DIR / f"CELL-00{index}" / "REPORT.md") for index in (1, 2, 3))
    for exp_id in ARTIFACT_IDS:
        paths.append(rel(RESULTS_DIR / f"{exp_id}.json"))
        paths.append(rel(RESULTS_DIR / f"{exp_id}.md"))
    return paths


def check_required_artifacts(root: Path | str = PROJECT_ROOT) -> Check:
    """
    Check that all required artifacts exist.

    :param root: Repository root.
    :return: Check result.
    """
    missing = [path for path in required_artifact_paths(root) if not path.is_file()]
    if missing:
        names = ", ".join(str(path.name) for path in missing[:5])
        return Check("required_artifacts", False, f"missing {len(missing)}: {names}")
    return Check("required_artifacts", True, f"{len(required_artifact_paths(root))} present")


def check_bridge_safety(root: Path | str = PROJECT_ROOT) -> Check:
    """
    Scan the bridge's runtime modules for dangerous execution patterns.

    :param root: Repository root.
    :return: Check result.
    """
    automation = Path(root) / "automation"
    hits: list[str] = []
    for module in SAFETY_SCAN_MODULES:
        path = automation / module
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                hits.append(f"{module}: {pattern}")
    if hits:
        return Check("bridge_safety", False, "; ".join(hits[:5]))
    return Check("bridge_safety", True, "no dangerous execution patterns")


def _artifact_digest(path: Path) -> str:
    """
    Digest an artifact, ignoring the ``generated_utc`` bookkeeping field.

    The committed diagnostic scripts stamp ``generated_utc`` on every run, so a
    faithful reproduction changes that field but not the measured numbers. The
    digest therefore canonicalises JSON after dropping the timestamp, while
    still detecting any substantive change.

    :param path: Artifact path.
    :return: SHA-256 hex digest.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if isinstance(data, dict):
        data.pop("generated_utc", None)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def snapshot_results(root: Path | str = PROJECT_ROOT) -> dict[str, str]:
    """
    Hash every tracked result artifact so a run can prove it changed nothing.

    JSON artifacts are canonicalised with ``generated_utc`` removed (see
    :func:`_artifact_digest`); other files are hashed byte-for-byte.

    :param root: Repository root.
    :return: Mapping of relative path to SHA-256.
    """
    base = Path(root)
    snapshot: dict[str, str] = {}
    for pattern in TRACKED_RESULT_GLOBS:
        for path in sorted(base.glob(pattern)):
            if not path.is_file():
                continue
            if path.suffix == ".json":
                digest = _artifact_digest(path)
            else:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[str(path.relative_to(base))] = digest
    return snapshot


def results_unchanged(before: dict[str, str], after: dict[str, str]) -> tuple[bool, list[str]]:
    """
    Compare two result snapshots.

    :param before: Snapshot taken before a run.
    :param after: Snapshot taken after a run.
    :return: ``(unchanged, changed_paths)``.
    """
    changed = sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )
    return not changed, changed


def run_validation(
    root: Path | str = PROJECT_ROOT,
    git_runner: GitRunner | None = None,
) -> ValidationResult:
    """
    Run the full validation suite.

    :param root: Repository root.
    :param git_runner: Injectable git runner.
    :return: Aggregate validation result.
    """
    result = ValidationResult()
    result.checks.append(check_gate_present(root))
    result.checks.append(check_production_untouched(root, git_runner))
    result.checks.append(check_required_artifacts(root))
    result.checks.append(check_json_artifacts(root))
    result.checks.append(check_bridge_safety(root))
    return result
