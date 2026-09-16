"""Rule-based signal generation for price-action momentum setups.

Signal generation is deliberately separated from risk management and execution.
Functions here answer exactly one question: *given candles, where is the setup?*
They know nothing about position size, stops, or account equity.

Every function is pure and causal; see :mod:`pa_indicators` for the causality
contract.
"""

from __future__ import annotations

import pandas as pd
from pa_indicators import donchian_lower, donchian_upper

__all__ = [
    "rising_edge",
    "donchian_breakout_frame",
    "turtle_entry_signals",
    "turtle_exit_signals",
]


def rising_edge(condition: pd.Series) -> pd.Series:
    """
    Mark bars where a boolean condition turns from False to True.

    This is the duplicate-signal guard used by every breakout family in this
    project. A close above the Donchian channel can remain true for many
    consecutive bars; without this filter each of those bars would emit a new
    entry and the strategy would silently pyramid.

    The first bar is never reported as an edge, even when the condition is
    already True there. Evidence of a preceding ``False`` is required, and on
    the very first bar that evidence does not exist -- the run may simply have
    started before the data began.

    :param condition: Boolean series.
    :return: Boolean series that is True only on the first bar of a run.
    """
    condition = condition.fillna(False).astype(bool)
    previous = condition.shift(1, fill_value=False).astype(bool)
    edge = condition & ~previous
    if len(edge):
        edge.iloc[0] = False
    return edge


def donchian_breakout_frame(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    entry_period: int = 20,
    exit_period: int = 10,
) -> pd.DataFrame:
    """
    Build the causal channel and breakout state for a Donchian system.

    Returned columns:

    ``dc_entry_upper``
        Prior ``entry_period``-bar highest high (excludes the current bar).
    ``dc_entry_lower``
        Prior ``entry_period``-bar lowest low (excludes the current bar).
    ``dc_exit_lower``
        Prior ``exit_period``-bar lowest low used for long exits.
    ``breakout_up``
        ``close > dc_entry_upper`` on the current bar.
    ``first_breakout_up``
        Rising edge of ``breakout_up`` (one signal per breakout episode).
    ``exit_long``
        ``close < dc_exit_lower``.

    :param high: High prices.
    :param low: Low prices.
    :param close: Close prices.
    :param entry_period: Donchian lookback for entries.
    :param exit_period: Donchian lookback for exits.
    :return: DataFrame aligned to the input index.
    """
    frame = pd.DataFrame(index=close.index)
    frame["dc_entry_upper"] = donchian_upper(high, entry_period)
    frame["dc_entry_lower"] = donchian_lower(low, entry_period)
    frame["dc_exit_lower"] = donchian_lower(low, exit_period)

    breakout_up = (close > frame["dc_entry_upper"]) & frame["dc_entry_upper"].notna()
    frame["breakout_up"] = breakout_up.fillna(False)
    frame["first_breakout_up"] = rising_edge(breakout_up)

    exit_long = (close < frame["dc_exit_lower"]) & frame["dc_exit_lower"].notna()
    frame["exit_long"] = exit_long.fillna(False)
    return frame


def turtle_entry_signals(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    entry_period: int = 20,
    exit_period: int = 10,
) -> pd.Series:
    """
    Long entry signal for the Turtle/Donchian baseline.

    Entry fires on the *first* bar whose close exceeds the prior
    ``entry_period``-bar high. De-duplication is intentional: it is part of the
    specification, not a tuning knob.

    :param high: High prices.
    :param low: Low prices.
    :param close: Close prices.
    :param entry_period: Donchian lookback for entries.
    :param exit_period: Donchian lookback for exits.
    :return: Boolean entry series.
    """
    frame = donchian_breakout_frame(high, low, close, entry_period, exit_period)
    return frame["first_breakout_up"]


def turtle_exit_signals(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    entry_period: int = 20,
    exit_period: int = 10,
) -> pd.Series:
    """
    Long exit signal for the Turtle/Donchian baseline.

    Exit fires when the close falls below the prior ``exit_period``-bar low.

    :param high: High prices.
    :param low: Low prices.
    :param close: Close prices.
    :param entry_period: Donchian lookback for entries.
    :param exit_period: Donchian lookback for exits.
    :return: Boolean exit series.
    """
    frame = donchian_breakout_frame(high, low, close, entry_period, exit_period)
    return frame["exit_long"]
