"""Causal price-action indicators for the PA momentum research programme.

Design rules enforced here:

1. Every function is pure: inputs are never mutated and no global state is used.
2. Every calculation is *causal*. A value produced for bar ``t`` may only use
   information from bars ``<= t``. Channel levels that feed a breakout decision
   are shifted by one bar so that a decision taken at bar ``t`` never consumes
   the high/low of bar ``t`` itself.
3. This module depends only on ``numpy`` and ``pandas``. It must never import
   ``freqtrade`` so that it stays cheap and deterministic to unit-test.

The one-bar shift is the single most important detail in this file: an
unshifted rolling maximum is a look-ahead bug that inflates backtest results
and is invisible unless causality is explicitly tested.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "true_range",
    "wilder_smooth",
    "atr",
    "rolling_high",
    "rolling_low",
    "donchian_upper",
    "donchian_lower",
    "donchian_mid",
    "donchian_width",
]


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Compute Wilder's true range.

    ``TR_t = max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)``

    The first bar has no previous close and therefore falls back to
    ``H_0 - L_0``.

    :param high: High prices.
    :param low: Low prices.
    :param close: Close prices.
    :return: True range series aligned to the input index.
    """
    prev_close = close.shift(1)
    hl = high - low
    hc = (high - prev_close).abs()
    lc = (low - prev_close).abs()
    # Row-wise max with skipna handles bar 0 automatically: the two
    # previous-close terms are NaN there, leaving H_0 - L_0.
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    tr.name = "true_range"
    return tr


def wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """
    Wilder's smoothing with a simple-moving-average seed.

    TA-Lib seeds the recursion with ``mean(x[0:period])`` at index
    ``period - 1`` and then applies
    ``y_t = ((period - 1) * y_{t-1} + x_t) / period``.

    A plain ``ewm(alpha=1/period, adjust=False)`` is *not* equivalent: it seeds
    with the first observation instead of the first ``period`` observations and
    therefore produces a different value at the seed bar. For a stop distance
    that is measured in ATRs, that difference matters, so the recursion is
    implemented explicitly to match TA-Lib.

    The first ``period - 1`` outputs are ``NaN`` so callers can never act on a
    partially-formed average.

    :param series: Input series.
    :param period: Lookback in bars. Must be >= 1.
    :return: Smoothed series aligned to the input index.
    :raises ValueError: If ``period`` is not a positive integer.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period!r}")
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    output = np.full(values.shape[0], np.nan, dtype=float)
    if values.shape[0] < period:
        return pd.Series(output, index=series.index, name=series.name)

    previous = float(np.nanmean(values[:period]))
    output[period - 1] = previous
    for index in range(period, values.shape[0]):
        previous = ((period - 1) * previous + values[index]) / period
        output[index] = previous
    return pd.Series(output, index=series.index, name=series.name)


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 20,
) -> pd.Series:
    """
    Wilder average true range, seeded like TA-Lib.

    :param high: High prices.
    :param low: Low prices.
    :param close: Close prices.
    :param period: Lookback in bars. Must be >= 1.
    :return: ATR series aligned to the input index.
    :raises ValueError: If ``period`` is not a positive integer.
    """
    tr = true_range(high, low, close)
    return wilder_smooth(tr, period)


def rolling_high(series: pd.Series, period: int, shift: int = 1) -> pd.Series:
    """
    Highest value over ``period`` bars, optionally shifted forward.

    :param series: Input series (typically ``high``).
    :param period: Lookback in bars. Must be >= 1.
    :param shift: Bars to shift the result forward. Defaults to 1 so the value
        at bar ``t`` covers ``[t - period - shift + 1, t - shift]``.
    :return: Rolling maximum series.
    :raises ValueError: If ``period`` is not a positive integer.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period!r}")
    return series.rolling(window=period, min_periods=period).max().shift(shift)


def rolling_low(series: pd.Series, period: int, shift: int = 1) -> pd.Series:
    """
    Lowest value over ``period`` bars, optionally shifted forward.

    :param series: Input series (typically ``low``).
    :param period: Lookback in bars. Must be >= 1.
    :param shift: Bars to shift the result forward. Defaults to 1.
    :return: Rolling minimum series.
    :raises ValueError: If ``period`` is not a positive integer.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period!r}")
    return series.rolling(window=period, min_periods=period).min().shift(shift)


def donchian_upper(high: pd.Series, period: int = 20, shift: int = 1) -> pd.Series:
    """
    Upper Donchian channel: the prior ``period``-bar highest high.

    With the default ``shift=1`` the value at bar ``t`` is
    ``max(high[t - period : t])``, i.e. it excludes bar ``t`` entirely. A close
    above this level is therefore a genuine breakout of *prior* price, not a
    comparison of a price against itself.

    :param high: High prices.
    :param period: Lookback in bars.
    :param shift: Bars to shift the result forward. Defaults to 1 (causal).
    :return: Upper channel series.
    """
    return rolling_high(high, period, shift=shift)


def donchian_lower(low: pd.Series, period: int = 20, shift: int = 1) -> pd.Series:
    """
    Lower Donchian channel: the prior ``period``-bar lowest low.

    See :func:`donchian_upper` for the causality contract.

    :param low: Low prices.
    :param period: Lookback in bars.
    :param shift: Bars to shift the result forward. Defaults to 1 (causal).
    :return: Lower channel series.
    """
    return rolling_low(low, period, shift=shift)


def donchian_mid(high: pd.Series, low: pd.Series, period: int = 20) -> pd.Series:
    """
    Midpoint of the causal upper and lower Donchian channel.

    :param high: High prices.
    :param low: Low prices.
    :param period: Lookback in bars.
    :return: Midpoint channel series.
    """
    return (donchian_upper(high, period) + donchian_lower(low, period)) / 2.0


def donchian_width(
    high: pd.Series,
    low: pd.Series,
    period: int = 20,
    normalise: bool = True,
) -> pd.Series:
    """
    Width of the Donchian channel, optionally normalised by its midpoint.

    The un-normalised width is a level that scales with price; the normalised
    width is a scale-free measure of local range size and is the more useful
    input for volatility-compression research.

    :param high: High prices.
    :param low: Low prices.
    :param period: Lookback in bars.
    :param normalise: Divide the width by the channel midpoint.
    :return: Channel width series.
    """
    upper = donchian_upper(high, period)
    lower = donchian_lower(low, period)
    width = upper - lower
    if not normalise:
        return width
    mid = (upper + lower) / 2.0
    return width / mid.replace(0.0, np.nan)
