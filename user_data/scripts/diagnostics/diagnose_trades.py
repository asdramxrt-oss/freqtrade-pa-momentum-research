"""PHASE 2 diagnostic: trade-level distributions, timing, stability and costs.

Re-runs the *frozen* strategies deterministically on labelled periods purely to
collect trade lists for descriptive measurement. It changes nothing and selects
nothing. The fresh-period runs must reproduce the recorded EXP-004 / EXP-001
numbers exactly; a mismatch is a bug to report, not to tune.

Usage::

    python user_data/scripts/diagnostics/diagnose_trades.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diag_common import PROJECT_ROOT, write_json  # noqa: E402
from exp003_backtest import analyse, load_latest_result, run_backtest  # noqa: E402

OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_trade_diagnostics.json"

RANGES = {
    "D_development": "20190101-20250101",
    "C_consumed_2025": "20250101-20260101",
    "F_fresh_2026": "20260101-20260916",
    "P_pooled_reference": "20190101-20260101",
}
STRATEGIES = {
    "turtle": "EXP-001.json",
    "pullback_long": "EXP-003-spot-long.json",
}
FEE = 0.0005


def _excerpts(trades: list[dict], is_short_key: bool = False) -> dict:
    """
    Per-trade excursions in percent from ``min_rate`` / ``max_rate``.

    :param trades: Exported trades.
    :param is_short_key: Unused placeholder for symmetry.
    :return: Mean/median MFE and MAE.
    """
    mfe, mae = [], []
    for trade in trades:
        open_rate = trade["open_rate"]
        high = trade.get("max_rate") or open_rate
        low = trade.get("min_rate") or open_rate
        mfe.append((high - open_rate) / open_rate * 100)
        mae.append((low - open_rate) / open_rate * 100)
    return {
        "mfe_mean_pct": float(np.mean(mfe)) if mfe else None,
        "mfe_median_pct": float(np.median(mfe)) if mfe else None,
        "mae_mean_pct": float(np.mean(mae)) if mae else None,
        "mae_median_pct": float(np.median(mae)) if mae else None,
    }


def _distribution(trades: list[dict]) -> dict:
    """
    Distribution and concentration statistics for one trade list.

    :param trades: Exported trades.
    :return: Descriptive statistics.
    """
    profits = np.array([t["profit_abs"] for t in trades], dtype=float)
    if profits.size == 0:
        return {"trades": 0}
    gross_profit = float(profits[profits > 0].sum())
    gross_loss = float(profits[profits < 0].sum())
    ordering = np.sort(profits)[::-1]
    wins = int((profits > 0).sum())
    losses = int((profits < 0).sum())
    durations = np.array([t["trade_duration"] for t in trades], dtype=float)
    win_durations = np.array(
        [t["trade_duration"] for t in trades if t["profit_abs"] > 0], dtype=float
    )
    loss_durations = np.array(
        [t["trade_duration"] for t in trades if t["profit_abs"] < 0], dtype=float
    )

    def top_contrib(fraction: float) -> float:
        """Share of gross profit contributed by the top ``fraction`` of trades."""
        count = max(1, int(np.ceil(fraction * profits.size)))
        return float(ordering[:count].sum() / gross_profit) if gross_profit > 0 else None

    def net_without_top(count: int) -> float:
        """Net profit with the largest ``count`` winners removed."""
        return float(profits.sum() - ordering[:count].sum())

    return {
        "trades": int(profits.size),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": wins / profits.size * 100,
        "net_profit_abs_usdt": float(profits.sum()),
        "expectancy_usdt": float(profits.mean()),
        "mean_trade_pct": float(np.mean([t["profit_ratio"] for t in trades]) * 100),
        "median_trade_pct": float(np.median([t["profit_ratio"] for t in trades]) * 100),
        "std_usdt": float(profits.std(ddof=1)) if profits.size > 1 else 0.0,
        "skew": float(stats.skew(profits)) if profits.size > 2 else None,
        "gross_profit_usdt": gross_profit,
        "gross_loss_usdt": gross_loss,
        "profit_factor": (gross_profit / abs(gross_loss)) if gross_loss < 0 else None,
        "win_loss_magnitude_ratio": (gross_profit / wins) / abs(gross_loss / losses)
        if wins and losses
        else None,
        "largest_winner_usdt": float(ordering[0]),
        "largest_loser_usdt": float(ordering[-1]),
        "largest_winner_share_of_gross": float(ordering[0] / gross_profit)
        if gross_profit > 0
        else None,
        "top1pct_share_of_gross": top_contrib(0.01),
        "top5pct_share_of_gross": top_contrib(0.05),
        "top10pct_share_of_gross": top_contrib(0.10),
        "net_without_top1_winner": net_without_top(1),
        "net_without_top3_winners": net_without_top(3),
        "net_without_top5_winners": net_without_top(5),
        "duration_median_min": float(np.median(durations)) if durations.size else None,
        "winner_duration_median_min": float(np.median(win_durations))
        if win_durations.size
        else None,
        "loser_duration_median_min": float(np.median(loss_durations))
        if loss_durations.size
        else None,
        "excursions": _excerpts(trades),
    }


def main() -> int:
    """
    Run the trade-level diagnostics and write the result.

    :return: Process exit code.
    """
    output = {
        "phase": "PHASE2",
        "generated_utc": datetime.now(UTC).isoformat(),
        "note": "frozen strategies re-run deterministically for measurement only",
        "strategies": {},
    }

    for strategy_name, config in STRATEGIES.items():
        output["strategies"][strategy_name] = {}
        for period, timerange in RANGES.items():
            run = {
                "label": f"diag-{strategy_name}-{period}",
                "config": config,
                "timerange": timerange,
                "fee": FEE,
            }
            run_backtest(run)
            result = load_latest_result()
            strategy_key = next(iter(result["strategy"]))
            trades = result["strategy"][strategy_key]["trades"]
            metrics = analyse(result)
            output["strategies"][strategy_name][period] = {
                "timerange": timerange,
                "wallet_max_drawdown_pct": metrics["max_drawdown_wallet_pct"],
                "market_change_pct": metrics["market_change_pct"],
                "turnover_usdt": metrics["turnover_usdt"],
                "fees_paid_usdt": metrics["fees_paid_usdt"],
                "time_in_market_ratio": metrics["time_in_market_ratio"],
                "p_value": metrics["p_value"],
                "distribution": _distribution(trades),
                "per_pair": metrics["results_per_pair"],
                "trade_profits_usdt": [round(t["profit_abs"], 6) for t in trades],
            }
            dist = output["strategies"][strategy_name][period]["distribution"]
            print(
                f"{strategy_name:14} {period:20} trades={dist['trades']:4} "
                f"PF={dist.get('profit_factor') if dist.get('profit_factor') is None else round(dist['profit_factor'], 3)} "
                f"exp={round(dist['expectancy_usdt'], 2) if dist['trades'] else None} "
                f"skew={None if dist.get('skew') is None else round(dist['skew'], 2)}"
            )

    write_json(OUTPUT, output)
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
