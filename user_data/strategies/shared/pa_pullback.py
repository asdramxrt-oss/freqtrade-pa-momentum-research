"""Pullback-continuation setup for EXP-003 (standalone, rule-based, no ML).

The setup is deliberately expressed in price-structure terms only: confirmed
swing points, ATR-normalised impulse and retracement, a structural-invalidation
level, and a continuation confirmation bar. No moving-average crossover, no RSI,
no MACD, no indicator confluence.

The exact rules are frozen in ``research/experiment_specs/EXP-003.md`` §4. This
module implements them and nothing else; it contains no position sizing, no stops
and no execution logic.

Every output is causal. Swing points are published only after their confirmation
delay (:mod:`pa_structure`), rolling extremes are trailing, and the final signal
is marked on a rising edge so one continuation episode produces one entry.
"""

from __future__ import annotations

import pandas as pd
from pa_indicators import atr, donchian_lower, donchian_upper
from pa_signals import rising_edge
from pa_structure import (
    bars_since_event,
    confirmed_swing_high,
    confirmed_swing_low,
    max_since_event,
    min_since_event,
    value_at_last_event,
)

__all__ = ["pullback_continuation_frame"]

# Frozen structural parameters (research/experiment_specs/EXP-003.md §5).
SWING_LEFT = 2
SWING_RIGHT = 2
ATR_PERIOD = 20
IMPULSE_MIN_ATR = 3.0
PULLBACK_MIN_ATR = 0.5
PULLBACK_MAX_ATR = 2.0
MAX_PULLBACK_BARS = 10
CONFIRM_BARS = 3
EXIT_PERIOD = 10


def pullback_continuation_frame(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    swing_left: int = SWING_LEFT,
    swing_right: int = SWING_RIGHT,
    atr_period: int = ATR_PERIOD,
    impulse_min_atr: float = IMPULSE_MIN_ATR,
    pullback_min_atr: float = PULLBACK_MIN_ATR,
    pullback_max_atr: float = PULLBACK_MAX_ATR,
    max_pullback_bars: int = MAX_PULLBACK_BARS,
    confirm_bars: int = CONFIRM_BARS,
    exit_period: int = EXIT_PERIOD,
) -> pd.DataFrame:
    """
    Build the pullback-continuation setup, signals and geometry.

    Signal columns (integers/booleans on the decision bar ``t``):

    ``long_signal`` / ``short_signal``
        Rising-edge entry signals for each direction.
    ``exit_long_signal`` / ``exit_short_signal``
        Causal Donchian channel exits.

    Geometry columns describe the setup that produced each decision bar, so that
    the experiment can analyse *which* pullbacks worked without re-tuning them.

    :param open_: Open prices.
    :param high: High prices.
    :param low: Low prices.
    :param close: Close prices.
    :param swing_left: Left bars for the swing pivot test.
    :param swing_right: Right bars (confirmation delay) for the swing pivot test.
    :param atr_period: ATR lookback used for all normalisation.
    :param impulse_min_atr: Minimum impulse size in ATR.
    :param pullback_min_atr: Minimum retracement in ATR.
    :param pullback_max_atr: Maximum retracement in ATR.
    :param max_pullback_bars: Maximum bars allowed between impulse high and entry.
    :param confirm_bars: Lookback for the continuation-confirmation break.
    :param exit_period: Donchian channel period used for exits.
    :return: DataFrame aligned to the input index.
    """
    frame = pd.DataFrame(index=close.index)
    frame["atr"] = atr(high, low, close, atr_period)

    # --- Causal structure -------------------------------------------------
    swing_high_pub = confirmed_swing_high(high, swing_left, swing_right)
    swing_low_pub = confirmed_swing_low(low, swing_left, swing_right)
    high_event = swing_high_pub.notna()
    low_event = swing_low_pub.notna()

    last_swing_high = swing_high_pub.ffill()
    last_swing_low = swing_low_pub.ffill()
    # Structural origins: the opposite swing that was current when the impulse
    # swing was published.
    origin_low = value_at_last_event(last_swing_low, high_event)
    origin_high = value_at_last_event(last_swing_high, low_event)

    bars_since_high = bars_since_event(high_event)
    bars_since_low = bars_since_event(low_event)
    atr_at_high = value_at_last_event(frame["atr"], high_event)
    atr_at_low = value_at_last_event(frame["atr"], low_event)
    min_low_since_high = min_since_event(low, high_event)
    max_high_since_low = max_since_event(high, low_event)

    frame["last_swing_high"] = last_swing_high
    frame["last_swing_low"] = last_swing_low
    frame["origin_low"] = origin_low
    frame["origin_high"] = origin_high

    prior_high = high.rolling(window=confirm_bars, min_periods=confirm_bars).max().shift(1)
    prior_low = low.rolling(window=confirm_bars, min_periods=confirm_bars).min().shift(1)

    # --- Long rules (spec §4.1) ------------------------------------------
    impulse_atr_long = (last_swing_high - origin_low) / atr_at_high
    depth_atr_long = (last_swing_high - close) / frame["atr"]
    impulse_ok_long = (last_swing_high > origin_low) & (impulse_atr_long >= impulse_min_atr)
    recency_ok_long = bars_since_high.between(1, max_pullback_bars)
    depth_ok_long = depth_atr_long.between(pullback_min_atr, pullback_max_atr)
    structure_ok_long = min_low_since_high > origin_low
    confirm_ok_long = (close > prior_high) & (close > open_)
    setup_long = (
        impulse_ok_long
        & recency_ok_long
        & depth_ok_long
        & structure_ok_long
        & confirm_ok_long
        & frame["atr"].notna()
    ).fillna(False)

    # --- Short rules (spec §4.2, exact mirror) ---------------------------
    impulse_atr_short = (origin_high - last_swing_low) / atr_at_low
    depth_atr_short = (close - last_swing_low) / frame["atr"]
    impulse_ok_short = (origin_high > last_swing_low) & (impulse_atr_short >= impulse_min_atr)
    recency_ok_short = bars_since_low.between(1, max_pullback_bars)
    depth_ok_short = depth_atr_short.between(pullback_min_atr, pullback_max_atr)
    structure_ok_short = max_high_since_low < origin_high
    confirm_ok_short = (close < prior_low) & (close < open_)
    setup_short = (
        impulse_ok_short
        & recency_ok_short
        & depth_ok_short
        & structure_ok_short
        & confirm_ok_short
        & frame["atr"].notna()
    ).fillna(False)

    frame["long_setup"] = setup_long
    frame["short_setup"] = setup_short
    frame["long_signal"] = rising_edge(setup_long)
    frame["short_signal"] = rising_edge(setup_short)

    # --- Exits (spec §4.3) ------------------------------------------------
    exit_lower = donchian_lower(low, exit_period)
    exit_upper = donchian_upper(high, exit_period)
    frame["exit_long_signal"] = ((close < exit_lower) & exit_lower.notna()).fillna(False)
    frame["exit_short_signal"] = ((close > exit_upper) & exit_upper.notna()).fillna(False)

    # --- Geometry (descriptive only; spec §10) ---------------------------
    frame["impulse_atr_long"] = impulse_atr_long
    frame["impulse_atr_short"] = impulse_atr_short
    frame["pullback_depth_atr_long"] = depth_atr_long
    frame["pullback_depth_atr_short"] = depth_atr_short
    frame["pullback_depth_pct_long"] = (last_swing_high - close) / last_swing_high
    frame["pullback_depth_pct_short"] = (close - last_swing_low) / last_swing_low
    frame["pullback_bars_long"] = bars_since_high
    frame["pullback_bars_short"] = bars_since_low
    frame["dist_from_structure_atr_long"] = (close - origin_low) / frame["atr"]
    frame["dist_from_structure_atr_short"] = (origin_high - close) / frame["atr"]
    frame["trigger_margin_atr_long"] = (close - prior_high) / frame["atr"]
    frame["trigger_margin_atr_short"] = (prior_low - close) / frame["atr"]
    frame["confirm_body_pct_long"] = (close - open_) / open_
    frame["confirm_body_pct_short"] = (open_ - close) / open_

    return frame
