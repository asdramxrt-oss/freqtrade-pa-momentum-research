"""EXP-002 cost sweep driver and fee attribution.

This script does exactly three things:

1. Executes the frozen EXP-002 backtest run list (timerange x fee), exactly as
   pre-registered in ``research/experiment_specs/EXP-002.md``.
2. Parses the exported freqtrade backtest result for each run.
3. Computes the transaction-cost metrics the research charter requires:
   turnover, entry/exit notional, total fees paid, fee drag, and the fee level at
   which the full-sample profit factor crosses 1.00.

It contains **no strategy logic**, chooses **no parameter**, and can only report
what the committed configuration produced. Running it again on the same data must
reproduce the recorded numbers.

Usage (from the project root, with freqtrade importable)::

    $env:PYTHONPATH = "C:\\path\\to\\freqtrade-develop"
    python user_data/scripts/exp002_cost_sweep.py

Optional::

    python user_data/scripts/exp002_cost_sweep.py --group full_sample
    python user_data/scripts/exp002_cost_sweep.py --group oos
    python user_data/scripts/exp002_cost_sweep.py --group per_year

The consolidated machine-readable output is written to
``research/experiment_results/EXP-002.raw.json``. Full freqtrade logs are written
to ``%TEMP%/pa-momentum-research/``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
USER_DATA = PROJECT_ROOT / "user_data"
RESULTS_DIR = USER_DATA / "backtest_results"
CONFIG = USER_DATA / "configs" / "EXP-002.json"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "EXP-002.raw.json"
LOG_DIR = Path(os.environ.get("TEMP", ".")) / "pa-momentum-research"

STRATEGY = "DonchianTurtleBaseline"

# --- Pre-registered run list (mirrors research/experiment_specs/EXP-002.md §7) ---
FULL_SAMPLE_FEES = [0.0005, 0.001, 0.002, 0.003, 0.005, 0.01]
OOS_FEES = [0.0005, 0.001, 0.002]
PER_YEAR_FEES = [0.0005, 0.001, 0.002]

FULL_SAMPLE_RANGE = "20190101-20260101"
OOS_RANGE = "20250101-20260101"
YEARS = list(range(2019, 2026))


def fee_tag(fee: float) -> str:
    """Return a filesystem/label-safe tag for a fee ratio (0.0025 -> '0p25')."""
    return f"{fee * 100:.2f}".replace(".", "p")


def build_run_list() -> list[dict]:
    """
    Build the frozen run list.

    :return: List of run descriptors (group, label, timerange, fee).
    """
    runs: list[dict] = []
    for fee in FULL_SAMPLE_FEES:
        runs.append(
            {
                "group": "full_sample",
                "label": f"full-sample-{fee_tag(fee)}",
                "timerange": FULL_SAMPLE_RANGE,
                "fee": fee,
            }
        )
    for fee in OOS_FEES:
        runs.append(
            {
                "group": "oos",
                "label": f"oos-{fee_tag(fee)}",
                "timerange": OOS_RANGE,
                "fee": fee,
            }
        )
    for year in YEARS:
        for fee in PER_YEAR_FEES:
            runs.append(
                {
                    "group": "per_year",
                    "year": year,
                    "label": f"{year}-{fee_tag(fee)}",
                    "timerange": f"{year}0101-{year + 1}0101",
                    "fee": fee,
                }
            )
    return runs


def run_backtest(run: dict) -> subprocess.CompletedProcess:
    """
    Execute one pre-registered backtest and return the completed process.

    :param run: Run descriptor from :func:`build_run_list`.
    :return: The completed subprocess (stdout/stderr captured).
    :raises RuntimeError: If freqtrade exits non-zero.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "freqtrade",
        "backtesting",
        "--userdir",
        str(USER_DATA),
        "-c",
        str(CONFIG),
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
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    log_file = LOG_DIR / f"EXP-002-{run['label']}.log"
    log_file.write_text(
        "$ " + " ".join(command) + "\n\n" + completed.stdout + "\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"backtest failed for {run['label']} (exit {completed.returncode}); "
            f"see {log_file}"
        )
    run["command"] = " ".join(command)
    run["log_file"] = str(log_file)
    return completed


def load_latest_result() -> dict:
    """
    Load the most recently exported freqtrade backtest result.

    Reads ``user_data/backtest_results/.last_result.json`` to find the newest
    export, then opens it whether it is a ``.json`` or a ``.zip`` archive.

    :return: Parsed backtest result dictionary.
    """
    pointer_file = RESULTS_DIR / ".last_result.json"
    pointer = json.loads(pointer_file.read_text(encoding="utf-8"))
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


def analyse(result: dict) -> dict:
    """
    Extract strategy-level metrics and compute cost attribution for one run.

    Fees are computed from the trade list as
    ``amount * open_rate * fee_open + amount * close_rate * fee_close`` and
    cross-checked against the per-order ``cost`` minus notional.

    :param result: Parsed freqtrade backtest result.
    :return: Flat metrics dictionary including turnover and fees paid.
    """
    strategy = result["strategy"][STRATEGY]
    trades = strategy["trades"]

    entry_notional = sum(t["amount"] * t["open_rate"] for t in trades)
    exit_notional = sum(t["amount"] * t["close_rate"] for t in trades)
    fee_from_trades = sum(
        t["amount"] * (t["open_rate"] * t["fee_open"] + t["close_rate"] * t["fee_close"])
        for t in trades
    )
    fee_from_orders = sum(
        order["cost"] - order["amount"] * order["safe_price"]
        for t in trades
        for order in t.get("orders", [])
    )

    starting = float(strategy["starting_balance"])
    net_profit_abs = float(strategy["profit_total_abs"])
    gross_profit_abs = net_profit_abs + fee_from_trades
    turnover = entry_notional + exit_notional

    per_pair = {
        row["key"]: {
            "trades": row["trades"],
            "profit_total_pct": row["profit_total"] * 100,
            "profit_total_abs": row["profit_total_abs"],
            "profit_factor": row.get("profit_factor", 0.0),
        }
        for row in strategy.get("results_per_pair", [])
        if row["key"] != "TOTAL"
    }

    return {
        "trades": strategy["total_trades"],
        "starting_balance": starting,
        "final_balance": float(strategy["final_balance"]),
        "net_profit_abs_usdt": net_profit_abs,
        "net_profit_pct": strategy["profit_total"] * 100,
        "cagr_pct": strategy["cagr"] * 100,
        "profit_factor": strategy["profit_factor"],
        "expectancy": strategy["expectancy"],
        "expectancy_ratio": strategy["expectancy_ratio"],
        "sharpe": strategy["sharpe"],
        "sortino": strategy["sortino"],
        "sqn": strategy["sqn"],
        "p_value": strategy["p_value"],
        "winrate_pct": strategy["winrate"] * 100,
        "wins": strategy["wins"],
        "losses": strategy["losses"],
        "draws": strategy["draws"],
        "max_drawdown_wallet_pct": strategy["max_drawdown_account"] * 100,
        "max_relative_drawdown_pct": strategy["max_relative_drawdown"] * 100,
        "market_change_pct": strategy["market_change"] * 100,
        "turnover_usdt": turnover,
        "turnover_reported_usdt": float(strategy["total_volume"]),
        "entry_notional_usdt": entry_notional,
        "exit_notional_usdt": exit_notional,
        "fees_paid_usdt": fee_from_trades,
        "fees_paid_orders_usdt": fee_from_orders,
        "fee_per_trade_usdt": fee_from_trades / len(trades) if trades else 0.0,
        "fee_drag_pct_of_start": fee_from_trades / starting * 100 if starting else 0.0,
        "gross_profit_abs_usdt": gross_profit_abs,
        "fees_pct_of_gross_profit": (
            fee_from_trades / gross_profit_abs * 100 if gross_profit_abs > 0 else None
        ),
        "results_per_pair": per_pair,
    }


def interpolate_breakeven(points: list[tuple[float, float]], target: float) -> float | None:
    """
    Linearly interpolate the x value where the series crosses ``target``.

    :param points: (x, y) pairs sorted by x.
    :param target: Target y value to cross.
    :return: Interpolated x, or ``None`` if the series never crosses.
    """
    ordered = sorted(points)
    for (x0, y0), (x1, y1) in zip(ordered, ordered[1:]):
        if (y0 - target) * (y1 - target) <= 0 and y1 != y0:
            return x0 + (target - y0) * (x1 - x0) / (y1 - y0)
    return None


def main() -> int:
    """
    Run the pre-registered sweep and write the consolidated raw result file.

    :return: Process exit code.
    """
    parser = argparse.ArgumentParser(description="EXP-002 cost sweep")
    parser.add_argument(
        "--group",
        choices=["all", "full_sample", "oos", "per_year"],
        default="all",
        help="Which pre-registered group to run.",
    )
    args = parser.parse_args()

    runs = [
        run
        for run in build_run_list()
        if args.group == "all" or run["group"] == args.group
    ]

    print(f"EXP-002 cost sweep: {len(runs)} runs")
    merged: dict[str, dict] = {}
    if OUTPUT.exists():
        prior = json.loads(OUTPUT.read_text(encoding="utf-8"))
        for record in prior.get("runs", []):
            merged[record["label"]] = record

    for index, run in enumerate(runs, start=1):
        print(f"  [{index}/{len(runs)}] {run['label']} fee={run['fee']:.4f} ...", flush=True)
        run_backtest(run)
        metrics = analyse(load_latest_result())
        record = dict(run)
        record["metrics"] = metrics
        merged[record["label"]] = record
        print(
            f"      trades={metrics['trades']} "
            f"PF={metrics['profit_factor']:.3f} "
            f"return={metrics['net_profit_pct']:.2f}% "
            f"fees={metrics['fees_paid_usdt']:,.0f} USDT",
            flush=True,
        )

    group_rank = {"full_sample": 0, "oos": 1, "per_year": 2}
    results = sorted(
        merged.values(),
        key=lambda r: (group_rank[r["group"]], r.get("year", 0), r["fee"]),
    )

    full_sample = [r for r in results if r["group"] == "full_sample"]
    breakeven = {
        "fee_at_pf_1_00": interpolate_breakeven(
            [(r["fee"], r["metrics"]["profit_factor"]) for r in full_sample], 1.0
        ),
        "fee_at_net_return_0": interpolate_breakeven(
            [(r["fee"], r["metrics"]["net_profit_pct"]) for r in full_sample], 0.0
        ),
    }

    output = {
        "experiment_id": "EXP-002",
        "strategy": STRATEGY,
        "config": str(CONFIG.relative_to(PROJECT_ROOT)),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run_count": len(results),
        "breakeven": breakeven,
        "runs": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nWrote {OUTPUT}")
    print(f"Breakeven (full sample): {breakeven}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
