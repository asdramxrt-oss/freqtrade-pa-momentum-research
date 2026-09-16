"""EXP-004 fresh-OOS runner (one-shot validation of the frozen long pullback).

Runs the frozen EXP-003 long-only configuration exactly once on the fresh,
previously unevaluated window ``20260101-20260916`` and records the required
metrics, per-pair and monthly breakdowns, and the pre-registered A1-A8
evaluation.

It does not change the strategy, parameters, universe, fee or window.

Usage::

    python user_data/scripts/exp004_oos.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "user_data" / "scripts"))

from exp003_backtest import analyse, load_latest_result, run_backtest  # noqa: E402

OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "EXP-004.raw.json"

FROZEN_CONFIG = "EXP-003-long.json"
FROZEN_STRATEGY_COMMIT = "c4bee8e264a111aa2e72dbce203bd49db1484d8b"
OOS_TIMERANGE = "20260101-20260916"
OOS_START = "2026-01-01"
OOS_END = "2026-09-16"
FEE = 0.0005


def _monthly(trades: list[dict]) -> dict:
    """
    Aggregate realised PnL by close month.

    :param trades: Exported trades.
    :return: Mapping ``YYYY-MM`` -> ``{trades, net_profit_abs_usdt}``.
    """
    buckets: dict[str, dict] = defaultdict(lambda: {"trades": 0, "net_profit_abs_usdt": 0.0})
    for trade in trades:
        month = trade["close_date"][:7]
        buckets[month]["trades"] += 1
        buckets[month]["net_profit_abs_usdt"] += trade["profit_abs"]
    return dict(sorted(buckets.items()))


def _win_loss_distribution(trades: list[dict]) -> dict:
    """
    Summarise the winning/losing trade distribution.

    :param trades: Exported trades.
    :return: Counts and profit extremes.
    """
    profits = sorted(t["profit_abs"] for t in trades)
    if not profits:
        return {"wins": 0, "losses": 0, "draws": 0}
    return {
        "wins": sum(1 for p in profits if p > 0),
        "losses": sum(1 for p in profits if p < 0),
        "draws": sum(1 for p in profits if p == 0),
        "best_usdt": profits[-1],
        "worst_usdt": profits[0],
    }


def _evaluate(metrics: dict, monthly: dict) -> dict:
    """
    Apply the pre-registered EXP-004 decision rule.

    :param metrics: Strategy metrics from :func:`analyse`.
    :param monthly: Monthly PnL breakdown.
    :return: Criteria table and verdict.
    """
    trades = metrics["trades"]
    profit_factor = metrics["profit_factor"]
    net_return = metrics["net_profit_pct"]
    p_value = metrics["p_value"]
    wallet_dd = metrics["max_drawdown_wallet_pct"]
    profitable_months = sum(1 for m in monthly.values() if m["net_profit_abs_usdt"] > 0)
    month_ratio = (profitable_months / len(monthly) * 100) if monthly else 0.0

    criteria = {
        "A1_min_trades": {"threshold": ">=200", "measured": trades, "pass": trades >= 200},
        "A2_profit_factor": {
            "threshold": ">=1.10",
            "measured": profit_factor,
            "pass": profit_factor >= 1.10,
        },
        "A3_expectancy_p_value": {
            "threshold": "<0.05",
            "measured": p_value,
            "pass": p_value < 0.05,
        },
        "A4_net_return": {"threshold": ">=0", "measured": net_return, "pass": net_return >= 0},
        "A5_profit_factor_ge_1": {
            "threshold": ">=1.00",
            "measured": profit_factor,
            "pass": profit_factor >= 1.00,
        },
        "A6_wallet_max_drawdown": {
            "threshold": "<35%",
            "measured": wallet_dd,
            "pass": wallet_dd < 35.0,
        },
        "A7_profitable_years": {
            "threshold": ">=60%",
            "measured": 100.0 if net_return >= 0 else 0.0,
            "pass": net_return >= 0,
        },
        "A8_profit_factor_stress": {
            "threshold": "N/A",
            "measured": None,
            "pass": None,
            "note": "not evaluated: no fee sweep in EXP-004",
        },
    }

    decisive_fail = (net_return < 0) or (profit_factor < 1.00)
    full_pass = all(
        value["pass"] is True for key, value in criteria.items() if key != "A8_profit_factor_stress"
    )
    if decisive_fail:
        verdict = "FAILS FRESH OOS"
    elif full_pass:
        verdict = "SURVIVES FRESH OOS"
    else:
        verdict = "INCONCLUSIVE / REQUIRES FURTHER VALIDATION"

    return {
        "criteria": criteria,
        "profitable_months": profitable_months,
        "total_months": len(monthly),
        "profitable_month_ratio_pct": month_ratio,
        "decisive_fail": decisive_fail,
        "full_pass": full_pass,
        "verdict": verdict,
    }


def main() -> int:
    """
    Run the one-shot fresh-OOS validation and write the result.

    :return: Process exit code.
    """
    run = {
        "label": "exp004-fresh-oos-long",
        "config": FROZEN_CONFIG,
        "strategy": "PullbackContinuationLong",
        "timerange": OOS_TIMERANGE,
        "fee": FEE,
    }
    run_backtest(run)
    result = load_latest_result()
    strategy_name = next(iter(result["strategy"]))
    trades = result["strategy"][strategy_name]["trades"]

    metrics = analyse(result)
    monthly = _monthly(trades)
    evaluation = _evaluate(metrics, monthly)

    output = {
        "experiment_id": "EXP-004",
        "objective": "fresh OOS validation of the frozen EXP-003 long-only pullback",
        "frozen_strategy_commit": FROZEN_STRATEGY_COMMIT,
        "config": f"user_data/configs/{FROZEN_CONFIG}",
        "strategy_class": strategy_name,
        "oos_timerange": OOS_TIMERANGE,
        "oos_start": OOS_START,
        "oos_end": OOS_END,
        "fee_per_side": FEE,
        "command": run["command"],
        "metrics": metrics,
        "monthly": monthly,
        "win_loss_distribution": _win_loss_distribution(trades),
        "evaluation": evaluation,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(
        f"trades={metrics['trades']} PF={metrics['profit_factor']:.4f} "
        f"net={metrics['net_profit_pct']:.2f}% p={metrics['p_value']:.5f} "
        f"ddW={metrics['max_drawdown_wallet_pct']:.2f}%"
    )
    print(f"VERDICT: {evaluation['verdict']}")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
