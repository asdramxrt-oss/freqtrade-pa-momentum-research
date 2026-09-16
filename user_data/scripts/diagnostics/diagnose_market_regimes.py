"""PHASE 2 diagnostic: market-regime comparison across periods.

Descriptive only. Volatility, trend persistence, range width, dispersion and
large-move frequency are measured per period; nothing here becomes a filter.

Usage::

    python user_data/scripts/diagnostics/diagnose_market_regimes.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diag_common import (  # noqa: E402
    PAIRS,
    PERIODS,
    PROJECT_ROOT,
    efficiency_ratio,
    load_candles,
    log_returns,
    run_lengths,
    slice_period,
    summarize,
    write_json,
)
from pa_indicators import atr, donchian_width  # noqa: E402

OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_market_regimes.json"


def _pair_metrics(frame: pd.DataFrame) -> dict:
    """
    Per-pair regime metrics for one period.

    :param frame: Period candle frame.
    :return: Scalar metrics.
    """
    close = frame["close"].astype(float)
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)
    returns = log_returns(close).dropna()
    atr_pct = (atr(high, low, close, 20) / close).dropna()
    width = donchian_width(high, low, 20, normalise=True).dropna()
    er = efficiency_ratio(close, 20).dropna()
    signs = np.sign(returns).replace(0, np.nan).dropna()
    continuation = (signs == signs.shift(1)).dropna()
    runs = run_lengths(signs)

    return {
        "bars": int(len(frame)),
        "market_return_pct": float(close.iloc[-1] / close.iloc[0] - 1.0) * 100,
        "realized_vol_4h": float(returns.std(ddof=1)) if len(returns) > 1 else None,
        "atr_pct_mean": float(atr_pct.mean()) if len(atr_pct) else None,
        "range_width_mean": float(width.mean()) if len(width) else None,
        "efficiency_ratio_mean": float(er.mean()) if len(er) else None,
        "autocorr_lag1": float(returns.autocorr(lag=1)) if len(returns) > 2 else None,
        "sign_continuation": float(continuation.mean()) if len(continuation) else None,
        "mean_run_length": float(runs.mean()) if len(runs) else None,
        "large_move_freq": float((returns.abs() > 4 * atr_pct.reindex(returns.index)).mean())
        if len(returns)
        else None,
    }


def _cross_sectional(period: str) -> dict:
    """
    Cross-sectional dispersion of 4h returns across pairs for one period.

    :param period: Period key.
    :return: Dispersion summary.
    """
    series = {}
    for symbol in PAIRS:
        frame = slice_period(load_candles(symbol), period)
        if frame.empty:
            continue
        series[symbol] = log_returns(frame["close"].astype(float)).set_axis(frame["date"])
    if not series:
        return {"mean_cross_sectional_std": None}
    wide = pd.DataFrame(series)
    per_bar = wide.std(axis=1, ddof=1).dropna()
    return {"mean_cross_sectional_std": float(per_bar.mean()), "bars": int(per_bar.size)}


def main() -> int:
    """
    Run the regime comparison and write the result.

    :return: Process exit code.
    """
    metrics = [
        "realized_vol_4h",
        "atr_pct_mean",
        "range_width_mean",
        "efficiency_ratio_mean",
        "autocorr_lag1",
        "sign_continuation",
        "mean_run_length",
        "large_move_freq",
    ]
    output = {
        "phase": "PHASE2",
        "generated_utc": datetime.now(UTC).isoformat(),
        "note": "descriptive only; no threshold is derived from these measurements",
        "periods": {},
    }

    for period in PERIODS:
        per_pair = {}
        for symbol in PAIRS:
            frame = slice_period(load_candles(symbol), period)
            if len(frame) < 30:
                continue
            per_pair[symbol] = _pair_metrics(frame)
        aggregate = {
            metric: summarize([p[metric] for p in per_pair.values() if p.get(metric) is not None])
            for metric in metrics
        }
        aggregate["market_return_pct_median"] = summarize(
            [p["market_return_pct"] for p in per_pair.values()]
        )
        output["periods"][period] = {
            "pair_count": len(per_pair),
            "per_pair": per_pair,
            "aggregate": aggregate,
            "cross_sectional": _cross_sectional(period),
        }

    write_json(OUTPUT, output)

    print(f"{'metric':26} {'D_dev':>10} {'C_2025':>10} {'F_2026':>10}")
    for metric in metrics + ["market_return_pct_median"]:
        row = []
        for period in ("D_development", "C_consumed_2025", "F_fresh_2026"):
            agg = output["periods"][period]["aggregate"].get(metric, {})
            row.append(agg.get("median"))
        print(f"{metric:26} {row[0]:>10.4f} {row[1]:>10.4f} {row[2]:>10.4f}")
    for period in ("D_development", "C_consumed_2025", "F_fresh_2026"):
        cs = output["periods"][period]["cross_sectional"]["mean_cross_sectional_std"]
        print(f"cross_sectional_std {period:22} {cs:.5f}")
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
