"""Shared helpers for the Phase 2 diagnostic analysis.

Diagnostics only: nothing here changes a strategy, and nothing here is used to
trade. The forward-looking helpers (``forward_excursions``) intentionally look
ahead *for measurement*, which is exactly what a post-mortem requires; they are
never used for signals or sizing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPOT_DIR = PROJECT_ROOT / "user_data" / "data" / "binance"
FUTURES_DIR = SPOT_DIR / "futures"
SHARED_DIR = PROJECT_ROOT / "user_data" / "strategies" / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

PAIRS = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LINK", "AVAX", "DOT"]

# Period labels and freqtrade-style timeranges. C and F are never pooled with D
# as independent evidence; P is a labelled non-independent reference.
PERIODS = {
    "D_development": ("2019-01-01", "2025-01-01"),
    "C_consumed_2025": ("2025-01-01", "2026-01-01"),
    "F_fresh_2026": ("2026-01-01", "2026-09-16"),
    "P_pooled_reference": ("2019-01-01", "2026-01-01"),
}

BARS_PER_DAY = 6
BARS_PER_YEAR = 365 * BARS_PER_DAY


def load_candles(symbol: str, futures: bool = False) -> pd.DataFrame:
    """
    Load one pair's 4h candles.

    :param symbol: Base symbol, e.g. ``BTC``.
    :param futures: Load the futures mirror instead of spot.
    :return: DataFrame with ``date, open, high, low, close, volume``.
    """
    folder = FUTURES_DIR if futures else SPOT_DIR
    suffix = "-4h-futures.feather" if futures else "-4h.feather"
    name = f"{symbol}_USDT_USDT{suffix}" if futures else f"{symbol}_USDT{suffix}"
    frame = pd.read_feather(folder / name)
    return frame.sort_values("date").reset_index(drop=True)


def slice_period(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    """
    Slice a candle frame to a labelled period.

    :param frame: Candle frame with a ``date`` column.
    :param period: Key of :data:`PERIODS`.
    :return: Sliced frame.
    """
    start, end = PERIODS[period]
    dates = pd.to_datetime(frame["date"], utc=True)
    mask = (dates >= pd.Timestamp(start, tz="UTC")) & (dates < pd.Timestamp(end, tz="UTC"))
    return frame.loc[mask].reset_index(drop=True)


def log_returns(close: pd.Series) -> pd.Series:
    """
    Log returns of a close series.

    :param close: Close prices.
    :return: Log-return series.
    """
    return np.log(close.astype(float)).diff()


def efficiency_ratio(close: pd.Series, window: int = 20) -> pd.Series:
    """
    Kaufman efficiency ratio over ``window`` bars (causal).

    :param close: Close prices.
    :param window: Lookback in bars.
    :return: Efficiency ratio in [0, 1].
    """
    change = (close - close.shift(window)).abs()
    path = close.diff().abs().rolling(window, min_periods=window).sum()
    return change / path.replace(0.0, np.nan)


def run_lengths(signs: pd.Series) -> pd.Series:
    """
    Length of each run of identical signs, broadcast to every bar in the run.

    :param signs: Series of ``-1``/``+1`` signs.
    :return: Series of run lengths aligned to ``signs``.
    """
    changed = signs.ne(signs.shift(1)).cumsum()
    return signs.groupby(changed).transform("size")


def forward_excursions(
    close: pd.Series, high: pd.Series, low: pd.Series, horizon: int
) -> pd.DataFrame:
    """
    Forward return, MFE and MAE over ``horizon`` bars, measured from close[t].

    Look-ahead by design (diagnostic measurement only).

    :param close: Close prices.
    :param high: High prices.
    :param low: Low prices.
    :param horizon: Forward window in bars.
    :return: DataFrame with ``fwd_ret``, ``mfe`` (ratios, >= 0) and ``mae`` (<= 0).
    """
    entry = close.astype(float)
    # Trailing max/min over ``horizon`` bars, shifted back so that index ``t``
    # covers bars ``t+1 .. t+horizon``.
    max_high = high.astype(float).rolling(horizon, min_periods=horizon).max().shift(-horizon)
    min_low = low.astype(float).rolling(horizon, min_periods=horizon).min().shift(-horizon)
    fwd_close = close.astype(float).shift(-horizon)
    return pd.DataFrame(
        {
            "fwd_ret": fwd_close / entry - 1.0,
            "mfe": max_high / entry - 1.0,
            "mae": min_low / entry - 1.0,
        }
    )


def summarize(values) -> dict:
    """
    Summarise a numeric sequence robustly.

    :param values: Iterable of numbers (NaNs dropped).
    :return: Distribution summary.
    """
    arr = pd.to_numeric(pd.Series(list(values)), errors="coerce").dropna()
    if arr.empty:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(arr.median()),
        "std": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        "p10": float(arr.quantile(0.10)),
        "p90": float(arr.quantile(0.90)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def bootstrap_ci(values, statistic=np.mean, iterations: int = 5000, seed: int = 12345):
    """
    Percentile bootstrap confidence interval.

    :param values: Sample values.
    :param statistic: Function applied to each resample.
    :param iterations: Number of bootstrap resamples.
    :param seed: RNG seed for reproducibility.
    :return: ``(low, high, point)`` at 95%.
    """
    arr = pd.to_numeric(pd.Series(list(values)), errors="coerce").dropna().to_numpy()
    if arr.size < 2:
        return {"point": float(statistic(arr)) if arr.size else None, "low": None, "high": None}
    rng = np.random.default_rng(seed)
    draws = np.array(
        [statistic(arr[rng.integers(0, arr.size, arr.size)]) for _ in range(iterations)]
    )
    return {
        "point": float(statistic(arr)),
        "low": float(np.quantile(draws, 0.025)),
        "high": float(np.quantile(draws, 0.975)),
        "iterations": iterations,
    }


def permutation_test(a, b, iterations: int = 10000, seed: int = 12345) -> dict:
    """
    Two-sided permutation test for a difference in means.

    :param a: Sample A.
    :param b: Sample B.
    :param iterations: Resamples.
    :param seed: RNG seed.
    :return: Observed difference, p-value and group sizes.
    """
    left = pd.to_numeric(pd.Series(list(a)), errors="coerce").dropna().to_numpy()
    right = pd.to_numeric(pd.Series(list(b)), errors="coerce").dropna().to_numpy()
    if left.size < 2 or right.size < 2:
        return {
            "observed_diff": None,
            "p_value": None,
            "n_a": int(left.size),
            "n_b": int(right.size),
        }
    observed = float(left.mean() - right.mean())
    pooled = np.concatenate([left, right])
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(iterations):
        rng.shuffle(pooled)
        diff = pooled[: left.size].mean() - pooled[left.size :].mean()
        if abs(diff) >= abs(observed):
            count += 1
    return {
        "observed_diff": observed,
        "p_value": (count + 1) / (iterations + 1),
        "n_a": int(left.size),
        "n_b": int(right.size),
        "iterations": iterations,
    }


def write_json(path: Path, payload: dict) -> None:
    """
    Write a JSON payload, creating parent directories.

    :param path: Destination path.
    :param payload: JSON-serialisable payload.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
