"""Causal price-structure primitives for the PA momentum research programme.

Everything here answers one question: *what does price structure look like using
only bars up to and including ``t``?* No swing point, no extreme and no elapsed
count may reference a future bar.

The central causality device is the **publication delay**. A swing high at bar
``i`` is only knowable once ``right`` bars have closed after it, so it is
*published* at bar ``i + right`` and is invisible before then. Strategies that
read a pivot at its own bar are look-ahead bugs; :func:`confirmed_swing_high`
makes that impossible by construction.

This module depends only on ``numpy`` and ``pandas`` and never imports
``freqtrade``, matching :mod:`pa_indicators`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "confirmed_swing_high",
    "confirmed_swing_low",
    "bars_since_event",
    "min_since_event",
    "max_since_event",
    "value_at_last_event",
]


def confirmed_swing_high(high: pd.Series, left: int = 2, right: int = 2) -> pd.Series:
    """
    Publish swing-high prices at the bar where they become knowable.

    Bar ``i`` is a swing high when ``high[i]`` is the maximum of
    ``high[i - left : i + right + 1]``. Because that test needs ``right`` future
    bars, the value is published at bar ``i + right`` and is ``NaN`` everywhere
    else. Forward-filling the result yields the most recent *confirmed* swing
    high at any bar.

    :param high: High price series.
    :param left: Bars to the left required to confirm the pivot. Must be >= 1.
    :param right: Bars to the right required to confirm the pivot. Must be >= 1.
    :return: Series with the pivot price on its confirmation bar, else ``NaN``.
    :raises ValueError: If ``left`` or ``right`` is not a positive integer.
    """
    if left < 1 or right < 1:
        raise ValueError(f"left and right must be >= 1, got {left!r}, {right!r}")
    window = left + right + 1
    # Trailing window whose right edge is the current bar.
    rolling_max = high.rolling(window=window, min_periods=window).max()
    # high[i] aligned to its confirmation bar i + right.
    candidate = high.shift(right)
    is_pivot = candidate >= rolling_max
    published = candidate.where(is_pivot)
    published.name = "confirmed_swing_high"
    return published


def confirmed_swing_low(low: pd.Series, left: int = 2, right: int = 2) -> pd.Series:
    """
    Publish swing-low prices at the bar where they become knowable.

    Mirror of :func:`confirmed_swing_high` using rolling minima.

    :param low: Low price series.
    :param left: Bars to the left required to confirm the pivot. Must be >= 1.
    :param right: Bars to the right required to confirm the pivot. Must be >= 1.
    :return: Series with the pivot price on its confirmation bar, else ``NaN``.
    :raises ValueError: If ``left`` or ``right`` is not a positive integer.
    """
    if left < 1 or right < 1:
        raise ValueError(f"left and right must be >= 1, got {left!r}, {right!r}")
    window = left + right + 1
    rolling_min = low.rolling(window=window, min_periods=window).min()
    candidate = low.shift(right)
    is_pivot = candidate <= rolling_min
    published = candidate.where(is_pivot)
    published.name = "confirmed_swing_low"
    return published


def bars_since_event(condition: pd.Series) -> pd.Series:
    """
    Count bars elapsed since the most recent ``True`` in ``condition``.

    The event bar itself is ``0``, the next bar is ``1``, and so on. Bars before
    the first event are ``NaN``. The count is causal: it only looks backwards.

    :param condition: Boolean event series. NaNs are treated as ``False``.
    :return: Float series of elapsed bars, ``NaN`` before the first event.
    """
    flags = condition.fillna(False).astype(bool)
    positions = pd.Series(np.arange(len(flags), dtype=float), index=flags.index)
    last_event = positions.where(flags).ffill()
    elapsed = positions - last_event
    elapsed.name = "bars_since_event"
    return elapsed


def min_since_event(values: pd.Series, condition: pd.Series) -> pd.Series:
    """
    Running minimum of ``values`` measured from the most recent event bar.

    At bar ``t`` the result is ``min(values[event .. t])`` where ``event`` is the
    most recent bar at or before ``t`` where ``condition`` was ``True``. Bars
    before the first event take the running minimum from the start of the series.

    :param values: Series to aggregate (typically ``low``).
    :param condition: Boolean event series. NaNs are treated as ``False``.
    :return: Running minimum since the last event, aligned to ``values``.
    """
    flags = condition.fillna(False).astype(bool)
    groups = flags.cumsum()
    result = values.groupby(groups).cummin()
    result.name = "min_since_event"
    return result


def max_since_event(values: pd.Series, condition: pd.Series) -> pd.Series:
    """
    Running maximum of ``values`` measured from the most recent event bar.

    Mirror of :func:`min_since_event`.

    :param values: Series to aggregate (typically ``high``).
    :param condition: Boolean event series. NaNs are treated as ``False``.
    :return: Running maximum since the last event, aligned to ``values``.
    """
    flags = condition.fillna(False).astype(bool)
    groups = flags.cumsum()
    result = values.groupby(groups).cummax()
    result.name = "max_since_event"
    return result


def value_at_last_event(values: pd.Series, condition: pd.Series) -> pd.Series:
    """
    Value of ``values`` at the most recent event bar, carried forward.

    Used to pair a published swing high with the structural level that was
    current when it was published (for example, the swing low that originated an
    impulse).

    :param values: Series to sample (typically a forward-filled level series).
    :param condition: Boolean event series. NaNs are treated as ``False``.
    :return: ``values`` sampled at the last event bar and forward-filled.
    """
    flags = condition.fillna(False).astype(bool)
    sampled = values.where(flags)
    result = sampled.ffill()
    result.name = "value_at_last_event"
    return result
