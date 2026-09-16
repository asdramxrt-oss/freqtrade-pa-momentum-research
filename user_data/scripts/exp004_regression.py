"""EXP-004 strategy-immutability regression.

Proves the frozen long-pullback implementation still reproduces EXP-003 exactly
on historical data, before the fresh out-of-sample window is touched.

Two checks:

1. Spot long-only, full EXP-003 sample (2019-01-01 -> 2026-01-01): every trade
   (pair, open timestamp, close timestamp, direction, profit, exit reason) is
   compared against the trades recorded in ``EXP-003.raw.json`` for
   ``spot-long-full``.
2. Futures long-only, same sample: aggregate trades / profit factor / return are
   compared against the recorded ``futures-long-full-0p05``.

The fresh OOS window is deliberately NOT used here.

Usage::

    python user_data/scripts/exp004_regression.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "user_data" / "scripts"))

from exp003_backtest import analyse, load_latest_result, run_backtest  # noqa: E402

RAW_RESULTS = PROJECT_ROOT / "research" / "experiment_results" / "EXP-003.raw.json"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "EXP-004.regression.json"


def _trades(result: dict) -> list[list]:
    """
    Extract trade tuples matching the stored EXP-003 entry layout.

    :param result: Parsed freqtrade backtest result.
    :return: List of ``[pair, open_ts, close_ts, is_short, profit_abs, exit_reason]``.
    """
    name = next(iter(result["strategy"]))
    return [
        [
            t["pair"],
            t["open_timestamp"],
            t["close_timestamp"],
            bool(t.get("is_short", False)),
            round(t["profit_abs"], 6),
            t["exit_reason"],
        ]
        for t in result["strategy"][name]["trades"]
    ]


def _compare_trades(expected: list[list], actual: list[list]) -> dict:
    """
    Compare two trade lists field by field.

    :param expected: Recorded trades.
    :param actual: Re-run trades.
    :return: Comparison summary.
    """
    expected_sorted = sorted(expected, key=lambda t: (t[0], t[1]))
    actual_sorted = sorted(actual, key=lambda t: (t[0], t[1]))
    mismatches = []
    for left, right in zip(expected_sorted, actual_sorted, strict=False):
        if left[:4] != right[:4] or abs(left[4] - right[4]) > 1e-3 or left[5] != right[5]:
            mismatches.append({"expected": left, "actual": right})
    return {
        "expected_trades": len(expected_sorted),
        "actual_trades": len(actual_sorted),
        "count_match": len(expected_sorted) == len(actual_sorted),
        "timestamp_and_value_mismatches": len(mismatches),
        "first_mismatches": mismatches[:5],
    }


def main() -> int:
    """
    Run the immutability regression and write the result.

    :return: Process exit code.
    """
    raw = json.loads(RAW_RESULTS.read_text(encoding="utf-8"))
    recorded = {r["label"]: r for r in raw["runs"]}

    # Check 1: spot long-only, full sample, exact trade comparison.
    spot_run = {
        "label": "regression-spot-long-full",
        "config": "EXP-003-spot-long.json",
        "timerange": "20190101-20260101",
        "fee": 0.0005,
    }
    run_backtest(spot_run)
    spot_result = load_latest_result()
    spot_trades = _trades(spot_result)
    spot_expected = recorded["spot-long-full"]["entry_timestamps"]
    spot_comparison = _compare_trades(spot_expected, spot_trades)

    # Check 2: futures long-only, full sample, aggregate comparison.
    futures_run = {
        "label": "regression-futures-long-full",
        "config": "EXP-003-long.json",
        "timerange": "20190101-20260101",
        "fee": 0.0005,
    }
    run_backtest(futures_run)
    futures_metrics = analyse(load_latest_result())
    futures_expected = recorded["futures-long-full-0p05"]["metrics"]
    futures_comparison = {
        "expected_trades": futures_expected["trades"],
        "actual_trades": futures_metrics["trades"],
        "expected_profit_factor": round(futures_expected["profit_factor"], 6),
        "actual_profit_factor": round(futures_metrics["profit_factor"], 6),
        "expected_net_profit_pct": round(futures_expected["net_profit_pct"], 4),
        "actual_net_profit_pct": round(futures_metrics["net_profit_pct"], 4),
    }
    futures_comparison["match"] = (
        futures_comparison["expected_trades"] == futures_comparison["actual_trades"]
        and abs(
            futures_comparison["expected_profit_factor"]
            - futures_comparison["actual_profit_factor"]
        )
        < 1e-4
        and abs(
            futures_comparison["expected_net_profit_pct"]
            - futures_comparison["actual_net_profit_pct"]
        )
        < 1e-2
    )

    output = {
        "experiment_id": "EXP-004",
        "purpose": "strategy immutability regression on historical EXP-003 data",
        "fresh_oos_used": False,
        "spot_long_full_exact_trade_comparison": spot_comparison,
        "futures_long_full_aggregate_comparison": futures_comparison,
        "passed": spot_comparison["count_match"]
        and spot_comparison["timestamp_and_value_mismatches"] == 0
        and futures_comparison["match"],
    }
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))
    print(f"\nWrote {OUTPUT}")
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
