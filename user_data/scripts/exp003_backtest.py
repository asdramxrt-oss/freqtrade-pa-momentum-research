"""EXP-003 backtest driver: runs the frozen EXP-003 run list and collects metrics.

Executes every pre-registered run from ``research/experiment_specs/EXP-003.md``
§7 and writes a consolidated, machine-readable result to
``research/experiment_results/EXP-003.raw.json``.

It contains **no strategy logic** and selects **no parameter**. It only runs the
committed configurations and reports what they produced, plus trade-level
breakdowns (long/short split, fees/turnover, MAE/MFE) and entry timestamps for the
descriptive complementarity analysis.

Usage (from the project root, with freqtrade importable)::

    $env:PYTHONPATH = "C:\\path\\to\\freqtrade-develop"
    python user_data/scripts/exp003_backtest.py
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
USER_DATA = PROJECT_ROOT / "user_data"
RESULTS_DIR = USER_DATA / "backtest_results"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "EXP-003.raw.json"
LOG_DIR = Path(os.environ.get("TEMP", ".")) / "pa-momentum-research"

FULL_RANGE = "20190101-20260101"
OOS_RANGE = "20250101-20260101"
YEARS = list(range(2019, 2026))

# (label, config, mode, direction) variants.
FUTURES_VARIANTS = [
    ("both", "EXP-003.json"),
    ("long", "EXP-003-long.json"),
    ("short", "EXP-003-short.json"),
]

CONFIG_BY_DIRECTION = {
    "both": "EXP-003.json",
    "long": "EXP-003-long.json",
    "short": "EXP-003-short.json",
}
STRATEGY_BY_DIRECTION = {
    "both": "PullbackContinuation",
    "long": "PullbackContinuationLong",
    "short": "PullbackContinuationShort",
}


def build_run_list() -> list[dict]:
    """
    Build the frozen EXP-003 run list.

    :return: List of run descriptors.
    """
    runs: list[dict] = []
    for direction in ("both", "long", "short"):
        for fee in (0.0005, 0.002):
            runs.append(
                {
                    "group": "full_sample",
                    "label": f"futures-{direction}-full-{_fee_tag(fee)}",
                    "direction": direction,
                    "config": CONFIG_BY_DIRECTION[direction],
                    "strategy": STRATEGY_BY_DIRECTION[direction],
                    "timerange": FULL_RANGE,
                    "fee": fee,
                    "capture_entries": direction == "both" and fee == 0.0005,
                }
            )
    for direction in ("both", "long", "short"):
        runs.append(
            {
                "group": "oos",
                "label": f"futures-{direction}-oos-{_fee_tag(0.0005)}",
                "direction": direction,
                "config": CONFIG_BY_DIRECTION[direction],
                "strategy": STRATEGY_BY_DIRECTION[direction],
                "timerange": OOS_RANGE,
                "fee": 0.0005,
                "capture_entries": False,
            }
        )
    for year in YEARS:
        for direction in ("both", "long", "short"):
            runs.append(
                {
                    "group": "per_year",
                    "year": year,
                    "label": f"futures-{direction}-{year}",
                    "direction": direction,
                    "config": CONFIG_BY_DIRECTION[direction],
                    "strategy": STRATEGY_BY_DIRECTION[direction],
                    "timerange": f"{year}0101-{year + 1}0101",
                    "fee": 0.0005,
                    "capture_entries": False,
                }
            )
    for timerange, tag in ((FULL_RANGE, "full"), (OOS_RANGE, "oos")):
        runs.append(
            {
                "group": "spot_control",
                "label": f"spot-long-{tag}",
                "direction": "long",
                "config": "EXP-003-spot-long.json",
                "strategy": "PullbackContinuationLong",
                "timerange": timerange,
                "fee": 0.0005,
                "capture_entries": tag == "full",
            }
        )
    runs.append(
        {
            "group": "turtle_ref",
            "label": "turtle-spot-long-full",
            "direction": "long",
            "config": "EXP-001.json",
            "strategy": "DonchianTurtleBaseline",
            "timerange": FULL_RANGE,
            "fee": 0.0005,
            "capture_entries": True,
        }
    )
    return runs


def _fee_tag(fee: float) -> str:
    """
    Return a label-safe tag for a fee ratio.

    :param fee: Fee per side as a ratio.
    :return: Tag such as ``0p05``.
    """
    return f"{fee * 100:.2f}".replace(".", "p")


def run_backtest(run: dict) -> None:
    """
    Execute one pre-registered backtest and record its command/log.

    :param run: Run descriptor.
    :raises RuntimeError: If freqtrade exits non-zero.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    config = USER_DATA / "configs" / run["config"]
    command = [
        sys.executable,
        "-m",
        "freqtrade",
        "backtesting",
        "--userdir",
        str(USER_DATA),
        "-c",
        str(config),
        "--timerange",
        run["timerange"],
        "--cache",
        "none",
        "--export",
        "trades",
        "--fee",
        repr(run["fee"]),
    ]
    completed = subprocess.run(
        command, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=os.environ.copy()
    )
    log_file = LOG_DIR / f"EXP-003-{run['label']}.log"
    log_file.write_text(
        "$ " + " ".join(command) + "\n\n" + completed.stdout + "\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"backtest failed for {run['label']} (exit {completed.returncode}); see {log_file}"
        )
    run["command"] = " ".join(command)
    run["log_file"] = str(log_file)


def load_latest_result() -> dict:
    """
    Load the most recently exported freqtrade backtest result.

    :return: Parsed backtest result dictionary.
    """
    pointer = json.loads((RESULTS_DIR / ".last_result.json").read_text(encoding="utf-8"))
    export = RESULTS_DIR / pointer["latest_backtest"]
    if export.suffix == ".zip":
        with zipfile.ZipFile(export) as archive:
            member = next(
                name
                for name in archive.namelist()
                if name.endswith(".json") and not name.endswith("_config.json")
            )
            return json.loads(archive.read(member))
    return json.loads(export.read_text(encoding="utf-8"))


def _side_stats(trades: list[dict], is_short: bool) -> dict:
    """
    Aggregate a direction's trades into profit-factor style statistics.

    :param trades: All trades for the run.
    :param is_short: Direction to select.
    :return: Aggregated statistics for that direction.
    """
    subset = [t for t in trades if bool(t.get("is_short", False)) == is_short]
    wins = sum(t["profit_abs"] for t in subset if t["profit_abs"] > 0)
    losses = sum(t["profit_abs"] for t in subset if t["profit_abs"] < 0)
    fees = sum(
        t["amount"] * (t["open_rate"] * t["fee_open"] + t["close_rate"] * t["fee_close"])
        for t in subset
    )
    turnover = sum(t["amount"] * (t["open_rate"] + t["close_rate"]) for t in subset)
    winner_count = sum(1 for t in subset if t["profit_abs"] > 0)
    return {
        "trades": len(subset),
        "net_profit_abs_usdt": float(sum(t["profit_abs"] for t in subset)),
        "profit_factor": (wins / abs(losses)) if losses else None,
        "win_count": winner_count,
        "win_rate_pct": (winner_count / len(subset) * 100) if subset else None,
        "fees_paid_usdt": fees,
        "turnover_usdt": turnover,
    }


def _excursion_stats(trades: list[dict]) -> dict:
    """
    Mean/median maximum adverse and favorable excursion, per direction.

    :param trades: All trades for the run.
    :return: Excursion statistics in percent.
    """
    result: dict[str, dict | None] = {}
    for name, is_short in (("long", False), ("short", True)):
        subset = [t for t in trades if bool(t.get("is_short", False)) == is_short]
        if not subset:
            result[name] = None
            continue
        mae = []
        mfe = []
        for trade in subset:
            open_rate = trade["open_rate"]
            min_rate = trade.get("min_rate") or open_rate
            max_rate = trade.get("max_rate") or open_rate
            if is_short:
                mae.append((max_rate - open_rate) / open_rate * 100)
                mfe.append((open_rate - min_rate) / open_rate * 100)
            else:
                mae.append((open_rate - min_rate) / open_rate * 100)
                mfe.append((max_rate - open_rate) / open_rate * 100)
        mae.sort()
        mfe.sort()
        result[name] = {
            "mae_mean_pct": sum(mae) / len(mae),
            "mae_median_pct": mae[len(mae) // 2],
            "mfe_mean_pct": sum(mfe) / len(mfe),
            "mfe_median_pct": mfe[len(mfe) // 2],
        }
    return result


def analyse(result: dict) -> dict:
    """
    Extract strategy metrics, direction breakdown, fees, turnover and excursions.

    :param result: Parsed freqtrade backtest result.
    :return: Flat metrics dictionary.
    """
    strategy_name = next(iter(result["strategy"]))
    strategy = result["strategy"][strategy_name]
    trades = strategy["trades"]

    fees = sum(
        t["amount"] * (t["open_rate"] * t["fee_open"] + t["close_rate"] * t["fee_close"])
        for t in trades
    )
    turnover = sum(t["amount"] * (t["open_rate"] + t["close_rate"]) for t in trades)
    duration_seconds = sum(t["trade_duration"] for t in trades) * 60.0
    backtest_seconds = float(strategy["backtest_days"]) * 86400.0

    metrics = {
        "strategy_class": strategy_name,
        "trades": strategy["total_trades"],
        "starting_balance": float(strategy["starting_balance"]),
        "final_balance": float(strategy["final_balance"]),
        "net_profit_abs_usdt": float(strategy["profit_total_abs"]),
        "net_profit_pct": strategy["profit_total"] * 100,
        "cagr_pct": strategy["cagr"] * 100,
        "profit_factor": strategy["profit_factor"],
        "expectancy": strategy["expectancy"],
        "expectancy_ratio": strategy["expectancy_ratio"],
        "avg_trade_pct": strategy["profit_mean"] * 100,
        "median_trade_pct": strategy["profit_median"] * 100,
        "sharpe": strategy["sharpe"],
        "sortino": strategy["sortino"],
        "sqn": strategy["sqn"],
        "p_value": strategy["p_value"],
        "winrate_pct": strategy["winrate"] * 100,
        "wins": strategy["wins"],
        "losses": strategy["losses"],
        "draws": strategy["draws"],
        "max_drawdown_trade_pct": strategy["max_relative_drawdown"] * 100,
        "max_drawdown_wallet_pct": strategy.get("wallet_stats", {}).get(
            "max_relative_drawdown", strategy["max_relative_drawdown"]
        )
        * 100,
        "holding_avg_seconds": strategy["holding_avg_s"],
        "market_change_pct": strategy["market_change"] * 100,
        "turnover_usdt": turnover,
        "fees_paid_usdt": fees,
        "time_in_market_ratio": (duration_seconds / backtest_seconds) if backtest_seconds else None,
        "long_side": _side_stats(trades, is_short=False),
        "short_side": _side_stats(trades, is_short=True),
        "excursions": _excursion_stats(trades),
        "results_per_pair": {
            row["key"]: {
                "trades": row["trades"],
                "net_profit_pct": row["profit_total"] * 100,
                "profit_factor": row.get("profit_factor", 0.0),
            }
            for row in strategy.get("results_per_pair", [])
            if row["key"] != "TOTAL"
        },
    }
    return metrics


def main() -> int:
    """
    Run the frozen EXP-003 sweep and write the consolidated raw result.

    :return: Process exit code.
    """
    parser = argparse.ArgumentParser(description="EXP-003 backtest sweep")
    parser.add_argument(
        "--group",
        choices=["all", "full_sample", "oos", "per_year", "spot_control", "turtle_ref"],
        default="all",
    )
    parser.add_argument("--only", default="", help="Run a single label only (diagnostics)")
    args = parser.parse_args()

    runs = [r for r in build_run_list() if args.group == "all" or r["group"] == args.group]
    if args.only:
        runs = [r for r in runs if r["label"] == args.only]
        if not runs:
            raise SystemExit(f"no run with label {args.only!r}")

    merged: dict[str, dict] = {}
    if OUTPUT.exists():
        prior = json.loads(OUTPUT.read_text(encoding="utf-8"))
        for record in prior.get("runs", []):
            merged[record["label"]] = record

    def persist() -> None:
        """Write the consolidated output, dropping any label not in the run list."""
        valid_labels = {r["label"] for r in build_run_list()}
        for label in [key for key in merged if key not in valid_labels]:
            del merged[label]
        order = {"full_sample": 0, "oos": 1, "per_year": 2, "spot_control": 3, "turtle_ref": 4}
        ordered = sorted(
            merged.values(),
            key=lambda r: (order[r["group"]], r.get("year", 0), r["direction"], r["fee"]),
        )
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(
                {
                    "experiment_id": "EXP-003",
                    "generated_utc": datetime.now(UTC).isoformat(),
                    "run_count": len(ordered),
                    "runs": ordered,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print(f"EXP-003 backtest sweep: {len(runs)} runs")
    for index, run in enumerate(runs, start=1):
        print(f"  [{index}/{len(runs)}] {run['label']} fee={run['fee']:.4f} ...", flush=True)
        run_backtest(run)
        result = load_latest_result()
        metrics = analyse(result)
        record = dict(run)
        record["metrics"] = metrics
        if run.get("capture_entries"):
            strategy_name = metrics["strategy_class"]
            # Entry tuple layout: [pair, open_ts, close_ts, is_short, profit_abs, exit_reason]
            record["entry_timestamps"] = [
                [
                    t["pair"],
                    t["open_timestamp"],
                    t["close_timestamp"],
                    bool(t.get("is_short", False)),
                    t["profit_abs"],
                    t["exit_reason"],
                ]
                for t in result["strategy"][strategy_name]["trades"]
            ]
        merged[record["label"]] = record
        persist()
        print(
            f"      trades={metrics['trades']} PF={metrics['profit_factor']} "
            f"ret={metrics['net_profit_pct']:.2f}% "
            f"long={metrics['long_side']['trades']} short={metrics['short_side']['trades']} "
            f"ddW={metrics['max_drawdown_wallet_pct']:.2f}%",
            flush=True,
        )

    persist()
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
