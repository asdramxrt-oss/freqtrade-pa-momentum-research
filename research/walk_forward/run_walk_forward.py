"""DEC-007 diagnostic-only walk-forward harness.

RESEARCH ONLY. This module contains **no strategy logic** and selects **no
parameter**. It subprocess-runs the *existing, unchanged* P3 research engines
over the windows frozen in ``walk_forward_config.json`` and reports per-window
performance, stability, decay and reproducibility.

Governance: DEC-007 (diagnostic-only). Frozen methodology:
``docs/FROZEN_IMPLEMENTATION_SPEC.md`` section 9 (anchored expanding in-sample,
1-year out-of-sample, 1-year step).

Results produced here are **diagnostic robustness evidence only**. They are not
validation, not a promotion and not a strategy verdict, and any window
overlapping 2025-2026 is non-pristine by construction.

Usage::

    python research/walk_forward/run_walk_forward.py --arm long_vol --repro-scope oos
    python research/walk_forward/run_walk_forward.py --arm all --repro-scope oos
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("walk_forward_config.json")
USER_DATA = PROJECT_ROOT / "user_data"
RESULTS_DIR = USER_DATA / "backtest_results"
LOG_DIR = Path(os.environ.get("TEMP", ".")) / "pa-momentum-research"

sys.path.insert(0, str(PROJECT_ROOT / "user_data" / "scripts"))

from exp003_backtest import analyse  # noqa: E402

METRIC_KEYS = (
    "net_profit_pct",
    "profit_factor",
    "trades",
    "max_drawdown_wallet_pct",
    "expectancy",
    "p_value",
    "winrate_pct",
    "sharpe",
)


def load_config(path: Path | str | None = None) -> dict:
    """
    Load the frozen walk-forward configuration.

    :param path: Config path (defaults to the file next to this module).
    :return: Parsed configuration.
    """
    target = Path(path) if path is not None else CONFIG_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def resolve_windows(config: dict) -> list[dict]:
    """
    Resolve the frozen windows into validated descriptors with timeranges.

    :param config: Parsed walk-forward configuration.
    :return: Window descriptors with ``is_timerange`` / ``oos_timerange``.
    :raises ValueError: When the anchor is inconsistent across windows.
    """
    anchor = str(config["methodology"]["is_anchor"])
    windows: list[dict] = []
    for window in config["windows"]:
        if str(window["is_start"]) != anchor:
            raise ValueError(
                f"window {window['id']} in-sample start {window['is_start']} != anchor {anchor}"
            )
        if window["is_end"] != window["oos_start"]:
            raise ValueError(f"window {window['id']} in-sample end must equal out-of-sample start")
        windows.append(
            {
                "id": window["id"],
                "label": window["label"],
                "is_start": window["is_start"],
                "is_end": window["is_end"],
                "oos_start": window["oos_start"],
                "oos_end": window["oos_end"],
                "is_timerange": f"{window['is_start']}-{window['is_end']}",
                "oos_timerange": f"{window['oos_start']}-{window['oos_end']}",
                "non_pristine": bool(window["non_pristine"]),
            }
        )
    return windows


def build_command(arm: dict, timerange: str, config: dict, strategy_path: Path) -> list[str]:
    """
    Build the exact freqtrade backtesting argv for one arm/window/phase.

    Mirrors ``user_data/scripts/p3_exp001_run.py`` and ``p3_exp003_carry.py``.

    :param arm: Arm descriptor from the config.
    :param timerange: freqtrade timerange string.
    :param config: Parsed walk-forward configuration.
    :param strategy_path: Directory containing the research strategies.
    :return: argv list.
    """
    return [
        sys.executable,
        "-m",
        "freqtrade",
        "backtesting",
        "--userdir",
        str(USER_DATA),
        "-d",
        str(PROJECT_ROOT / config["dataset"]),
        "--strategy-path",
        str(strategy_path),
        "-c",
        str(PROJECT_ROOT / arm["config"]),
        "--strategy",
        arm["strategy"],
        "--timerange",
        timerange,
        "--cache",
        "none",
        "--export",
        "trades",
        "--fee",
        repr(float(config["fee"])),
    ]


def parse_latest_result(results_dir: Path | None = None) -> dict:
    """
    Read the most recently exported freqtrade backtest result.

    :param results_dir: Directory holding ``.last_result.json``.
    :return: Parsed result dictionary.
    """
    directory = results_dir if results_dir is not None else RESULTS_DIR
    pointer = json.loads((directory / ".last_result.json").read_text(encoding="utf-8"))
    export = directory / pointer["latest_backtest"]
    if export.suffix == ".zip":
        with zipfile.ZipFile(export) as archive:
            member = next(
                name
                for name in archive.namelist()
                if name.endswith(".json") and not name.endswith("_config.json")
            )
            return json.loads(archive.read(member))
    return json.loads(export.read_text(encoding="utf-8"))


def funding_pnl(result: dict) -> float:
    """
    Total funding PnL the engine applied across all trades.

    :param result: Parsed freqtrade backtest result.
    :return: Sum of ``funding_fees`` in quote currency.
    """
    strategy_name = next(iter(result["strategy"]))
    trades = result["strategy"][strategy_name]["trades"]
    return float(sum(t.get("funding_fees", 0.0) or 0.0 for t in trades))


def run_backtest(command: list[str], label: str) -> dict:
    """
    Execute one backtest and return its parsed result.

    :param command: argv list.
    :param label: Log label.
    :return: Parsed backtest result.
    :raises RuntimeError: On a non-zero freqtrade exit.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=os.environ.copy()
    )
    log_file = LOG_DIR / f"dec007-{label}.log"
    log_file.write_text(
        "$ " + " ".join(command) + "\n\n" + completed.stdout + "\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"backtest failed for {label}; see {log_file}")
    return parse_latest_result()


def summarise(result: dict) -> dict:
    """
    Reduce a parsed backtest result to the reported metrics.

    :param result: Parsed freqtrade backtest result.
    :return: Flat metric dictionary including applied funding.
    """
    metrics = analyse(result)
    summary = {key: metrics.get(key) for key in METRIC_KEYS}
    summary["strategy_class"] = metrics.get("strategy_class")
    summary["funding_fees_applied_usdt"] = funding_pnl(result)
    return summary


def compute_stability(oos_records: list[dict]) -> dict:
    """
    Summarise out-of-sample stability for one arm across windows.

    :param oos_records: Per-window OOS metric dictionaries (ordered).
    :return: Stability summary.
    """
    if not oos_records:
        return {"windows": 0}
    returns = [float(r["net_profit_pct"]) for r in oos_records]
    pfs = [float(r["profit_factor"]) for r in oos_records if r.get("profit_factor") is not None]
    positives = sum(1 for value in returns if value > 0)
    signs = {value > 0 for value in returns}
    return {
        "windows": len(returns),
        "positive_windows": positives,
        "positive_fraction": positives / len(returns),
        "sign_consistent": len(signs) == 1,
        "return_min_pct": min(returns),
        "return_max_pct": max(returns),
        "return_mean_pct": sum(returns) / len(returns),
        "pf_min": min(pfs) if pfs else None,
        "pf_max": max(pfs) if pfs else None,
        "pf_mean": (sum(pfs) / len(pfs)) if pfs else None,
        "pf_range": (max(pfs) - min(pfs)) if pfs else None,
    }


def compute_decay(window_records: list[dict]) -> dict:
    """
    In-sample versus out-of-sample decay for one arm.

    :param window_records: Per-window dicts with ``is_metrics`` and ``oos_metrics``.
    :return: Decay summary with per-window ratios.
    """
    per_window: list[dict] = []
    ratios: list[float] = []
    for record in window_records:
        is_metrics = record["is_metrics"]
        oos_metrics = record["oos_metrics"]
        is_exp = _as_float(is_metrics.get("expectancy"))
        oos_exp = _as_float(oos_metrics.get("expectancy"))
        ratio = None
        if is_exp not in (None, 0.0) and oos_exp is not None:
            ratio = oos_exp / is_exp
            ratios.append(ratio)
        per_window.append(
            {
                "window": record["window"],
                "is_expectancy": is_exp,
                "oos_expectancy": oos_exp,
                "oos_over_is_expectancy": ratio,
                "is_return_pct": _as_float(is_metrics.get("net_profit_pct")),
                "oos_return_pct": _as_float(oos_metrics.get("net_profit_pct")),
            }
        )
    return {
        "per_window": per_window,
        "mean_oos_over_is_expectancy": (sum(ratios) / len(ratios)) if ratios else None,
    }


def _canonical_key(run_key: str) -> str:
    """
    Strip the pass suffix so pass 1 and pass 2 runs of the same run align.

    :param run_key: Run key, optionally ending in ``|passN``.
    :return: Canonical key.
    """
    return run_key.rsplit("|pass", 1)[0] if "|pass" in run_key else run_key


def assert_reproducible(pass1: dict, pass2: dict) -> None:
    """
    Assert two passes produced identical metrics for every shared run.

    Keys may include a ``|passN`` suffix; runs are aligned on their canonical
    (pass-independent) key.

    :param pass1: Run mapping from pass 1.
    :param pass2: Run mapping from pass 2.
    :raises AssertionError: When metrics differ, or when nothing matches.
    """
    pass2_by_key = {_canonical_key(key): value for key, value in pass2.items()}
    compared = 0
    for key, record in pass1.items():
        canonical = _canonical_key(key)
        if canonical not in pass2_by_key:
            continue
        left = record["metrics"]
        right = pass2_by_key[canonical]["metrics"]
        for metric in METRIC_KEYS:
            if left.get(metric) != right.get(metric):
                raise AssertionError(
                    f"reproducibility mismatch for {canonical} metric {metric}: "
                    f"{left.get(metric)!r} != {right.get(metric)!r}"
                )
        compared += 1
    if compared == 0 and pass1 and pass2:
        raise AssertionError("reproducibility comparison found no matching runs")


def _as_float(value: object) -> float | None:
    """
    Coerce a metric to float when possible.

    :param value: Raw value.
    :return: Float or None.
    """
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _fmt(value: object, digits: int = 4) -> str:
    """
    Format a metric for the report, tolerating missing values.

    :param value: Raw value.
    :param digits: Decimal places.
    :return: Formatted string or ``n/a``.
    """
    number = _as_float(value)
    return "n/a" if number is None else f"{number:.{digits}f}"


def _run_key(arm: str, window: str, phase: str, pass_no: int) -> str:
    """
    Build the stable key for one run.

    :param arm: Arm key.
    :param window: Window id.
    :param phase: ``is`` or ``oos``.
    :param pass_no: Pass number.
    :return: Run key.
    """
    return f"{arm}|{window}|{phase}|pass{pass_no}"


def execute(config: dict, arms: list[str], passes: int, repro_scope: str, force: bool) -> dict:
    """
    Run the requested arms/windows and persist the raw run records.

    :param config: Parsed configuration.
    :param arms: Arm keys to run.
    :param passes: Number of reproducibility passes (1 or 2).
    :param repro_scope: ``all`` or ``oos`` (which phase pass 2 repeats).
    :param force: Re-run existing keys.
    :return: Raw output document.
    """
    raw_path = PROJECT_ROOT / config["outputs"]["raw"]
    windows = resolve_windows(config)
    strategy_path = PROJECT_ROOT / config["strategy_path"]
    raw: dict = {
        "experiment_id": config["experiment_id"],
        "governance_ref": config["governance_ref"],
        "diagnostic_only": True,
        "generated_utc": datetime.now(UTC).isoformat(),
        "runs": {},
    }
    if raw_path.exists():
        prior = json.loads(raw_path.read_text(encoding="utf-8"))
        raw["runs"] = prior.get("runs", {})

    for arm_key in arms:
        arm = config["arms"][arm_key]
        for window in windows:
            for phase, timerange in (
                ("is", window["is_timerange"]),
                ("oos", window["oos_timerange"]),
            ):
                for pass_no in range(1, passes + 1):
                    if pass_no == 2 and repro_scope == "oos" and phase != "oos":
                        continue
                    key = _run_key(arm_key, window["id"], phase, pass_no)
                    if key in raw["runs"] and not force:
                        print(f"  skip (present) {key}", flush=True)
                        continue
                    label = f"{arm_key}-{window['id']}-{phase}-p{pass_no}"
                    print(f"  run  {key} [{timerange}] ...", flush=True)
                    command = build_command(arm, timerange, config, strategy_path)
                    result = run_backtest(command, label)
                    raw["runs"][key] = {
                        "arm": arm_key,
                        "strategy": arm["strategy"],
                        "experiment": arm["experiment"],
                        "window": window["id"],
                        "phase": phase,
                        "timerange": timerange,
                        "non_pristine": window["non_pristine"],
                        "command": " ".join(command),
                        "metrics": summarise(result),
                    }
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
                    summary = raw["runs"][key]["metrics"]
                    print(
                        f"      trades={summary['trades']} PF={summary['profit_factor']} "
                        f"ret={summary['net_profit_pct']:.2f}% "
                        f"ddW={summary['max_drawdown_wallet_pct']:.2f}%",
                        flush=True,
                    )
    return raw


def consolidate(config: dict, raw: dict, checks: dict) -> dict:
    """
    Build the consolidated per-arm report document.

    :param config: Parsed configuration.
    :param raw: Raw run document.
    :param checks: Reproducibility summary.
    :return: Consolidated document.
    """
    arms_out: dict = {}
    for arm_key in config["arms"]:
        window_records: list[dict] = []
        for window in resolve_windows(config):
            is_metrics = _metrics(raw, arm_key, window["id"], "is", 1)
            oos_metrics = _metrics(raw, arm_key, window["id"], "oos", 1)
            if is_metrics is None or oos_metrics is None:
                continue
            window_records.append(
                {
                    "window": window["id"],
                    "label": window["label"],
                    "non_pristine": window["non_pristine"],
                    "is_timerange": window["is_timerange"],
                    "oos_timerange": window["oos_timerange"],
                    "is_metrics": is_metrics,
                    "oos_metrics": oos_metrics,
                }
            )
        if not window_records:
            continue
        arms_out[arm_key] = {
            "strategy": config["arms"][arm_key]["strategy"],
            "experiment": config["arms"][arm_key]["experiment"],
            "windows": window_records,
            "oos_stability": compute_stability([r["oos_metrics"] for r in window_records]),
            "decay": compute_decay(window_records),
        }
    return {
        "experiment_id": config["experiment_id"],
        "governance_ref": config["governance_ref"],
        "diagnostic_only": True,
        "generated_utc": datetime.now(UTC).isoformat(),
        "non_pristine_windows": [w["id"] for w in resolve_windows(config) if w["non_pristine"]],
        "reproducibility": checks,
        "arms": arms_out,
    }


def _metrics(raw: dict, arm: str, window: str, phase: str, pass_no: int) -> dict | None:
    """
    Look up one run's metrics in the raw document.

    :param raw: Raw run document.
    :param arm: Arm key.
    :param window: Window id.
    :param phase: ``is`` or ``oos``.
    :param pass_no: Pass number.
    :return: Metrics dict or None.
    """
    record = raw["runs"].get(_run_key(arm, window, phase, pass_no))
    return record["metrics"] if record else None


def write_report(config: dict, consolidated: dict) -> Path:
    """
    Write the human-readable diagnostic report and return its path.

    :param config: Parsed configuration.
    :param consolidated: Consolidated document.
    :return: Report path.
    """
    report_path = PROJECT_ROOT / config["outputs"]["report"]
    lines: list[str] = []
    lines.append("# DEC-007 — diagnostic-only walk-forward")
    lines.append("")
    lines.append(
        "**Status:** DIAGNOSTIC ONLY. This is not validation, not a promotion and"
        " not a strategy verdict. All engines were already FAIL on their"
        " preregistered criteria (P3-EXP-001 long arms, P3-EXP-003 carry)."
    )
    lines.append("")
    lines.append(
        "Frozen methodology: `docs/FROZEN_IMPLEMENTATION_SPEC.md` section 9"
        " (anchored expanding in-sample, 1-year out-of-sample, 1-year step)."
        " Governance: DEC-007. Windows are frozen in"
        " `research/walk_forward/walk_forward_config.json` before execution."
    )
    lines.append("")
    lines.append(
        "**NON-PRISTINE:** windows "
        + ", ".join(consolidated["non_pristine_windows"])
        + " overlap the 2025-2026 period already observed by EXP-001..004 and"
        " PHASE 2. They are reported as non-pristine diagnostics, never as clean"
        " out-of-sample evidence."
    )
    lines.append("")
    for arm_key, arm in consolidated["arms"].items():
        lines.append(f"## {arm_key} — {arm['strategy']} ({arm['experiment']})")
        lines.append("")
        lines.append(
            "| Window | Pristine? | IS trades | IS PF | IS ret % | OOS trades |"
            " OOS PF | OOS ret % | OOS DD % | OOS expectancy | OOS p | OOS funding USDT |"
        )
        lines.append(
            "|--------|-----------|----------:|------:|---------:|-----------:|"
            "-------:|----------:|---------:|---------------:|------:|----------------:|"
        )
        for record in arm["windows"]:
            is_m = record["is_metrics"]
            oos_m = record["oos_metrics"]
            lines.append(
                f"| {record['window']} ({record['label']}) |"
                f" {'NO' if record['non_pristine'] else 'yes'} |"
                f" {is_m['trades']} | {_fmt(is_m['profit_factor'])} |"
                f" {is_m['net_profit_pct']:.2f} | {oos_m['trades']} |"
                f" {_fmt(oos_m['profit_factor'])} | {oos_m['net_profit_pct']:.2f} |"
                f" {oos_m['max_drawdown_wallet_pct']:.2f} |"
                f" {_fmt(oos_m['expectancy'])} | {_fmt(oos_m['p_value'])} |"
                f" {_fmt(oos_m.get('funding_fees_applied_usdt'), 2)} |"
            )
        stability = arm["oos_stability"]
        lines.append("")
        lines.append(
            f"**OBSERVED FACT (stability):** {stability.get('positive_windows')}/"
            f"{stability.get('windows')} OOS windows positive;"
            f" sign-consistent = {stability.get('sign_consistent')};"
            f" OOS PF range = {_fmt(stability.get('pf_range'))};"
            f" OOS return range = [{stability.get('return_min_pct'):.2f}%,"
            f" {stability.get('return_max_pct'):.2f}%]."
        )
        decay = arm["decay"]
        mean_decay = decay.get("mean_oos_over_is_expectancy")
        lines.append(
            f"**OBSERVED FACT (decay):** mean OOS/IS expectancy ratio = {_fmt(mean_decay)}."
        )
        lines.append(
            "**NOT APPLICABLE (parameter drift):** no parameter was selected or"
            " tuned on any window; the engines use frozen fixed parameters."
        )
        lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    lines.append(f"```json\n{json.dumps(consolidated['reproducibility'], indent=2)}\n```")
    lines.append("")
    lines.append(
        "## LIMITATIONS\n\n"
        "- Diagnostic only; no engine here passed its preregistered criteria.\n"
        "- 2025-2026 windows are non-pristine (already consumed).\n"
        "- No pristine post-2026-09 holdout exists (SI-2).\n"
        "- Early windows are dominated by the first-listed pairs; later-listed"
        " pairs are absent before their listing date.\n"
        "- No parameter search was performed, so this cannot select a"
        " configuration."
    )
    lines.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    """
    CLI entry point.

    :return: Process exit code.
    """
    parser = argparse.ArgumentParser(description="DEC-007 diagnostic walk-forward")
    parser.add_argument("--arm", default="all", help="arm key or 'all'")
    parser.add_argument("--passes", type=int, default=2, choices=[1, 2])
    parser.add_argument("--repro-scope", default="oos", choices=["all", "oos"])
    parser.add_argument("--force", action="store_true", help="re-run existing keys")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    args = parser.parse_args()

    config = load_config(args.config)
    arms = list(config["arms"]) if args.arm == "all" else [args.arm]
    for arm_key in arms:
        if arm_key not in config["arms"]:
            raise SystemExit(f"unknown arm {arm_key!r}")

    raw = execute(config, arms, args.passes, args.repro_scope, args.force)

    pass1 = {k: v for k, v in raw["runs"].items() if k.endswith("|pass1")}
    pass2 = {k: v for k, v in raw["runs"].items() if k.endswith("|pass2")}
    checks = {"passes_present": sorted({k.split("|")[-1] for k in raw["runs"]})}
    if pass2:
        assert_reproducible(pass1, pass2)
        checks["result"] = "IDENTICAL"
        checks["compared_runs"] = len(pass2)
    else:
        checks["result"] = "NOT_RUN"

    consolidated = consolidate(config, raw, checks)
    consolidated_path = PROJECT_ROOT / config["outputs"]["consolidated"]
    consolidated_path.write_text(json.dumps(consolidated, indent=2), encoding="utf-8")
    report_path = write_report(config, consolidated)
    print(f"\nWrote {consolidated_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
