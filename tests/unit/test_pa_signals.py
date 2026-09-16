"""Unit tests for rule-based signal generation."""

from __future__ import annotations

import pandas as pd
import pytest
from pa_signals import (
    donchian_breakout_frame,
    rising_edge,
    turtle_entry_signals,
    turtle_exit_signals,
)

from tests.helpers import make_candles


class TestRisingEdge:
    """Duplicate-signal suppression."""

    def test_marks_only_first_true_of_each_run(self) -> None:
        condition = pd.Series([False, False, True, True, False, True, True])

        result = rising_edge(condition)

        assert result.tolist() == [False, False, True, False, False, True, False]

    def test_all_false_stays_false(self) -> None:
        condition = pd.Series([False, False, False])

        assert not rising_edge(condition).any()

    def test_first_bar_is_never_an_edge(self) -> None:
        condition = pd.Series([True, True])

        assert rising_edge(condition).tolist() == [False, False]

    def test_nan_is_treated_as_false(self) -> None:
        condition = pd.Series([float("nan"), True, True])

        assert rising_edge(condition).tolist() == [False, True, False]


class TestDonchianBreakoutFrame:
    """Channel and state construction."""

    def test_exposes_expected_columns(self) -> None:
        candles = make_candles([100.0] * 30)

        frame = donchian_breakout_frame(candles["high"], candles["low"], candles["close"])

        assert set(frame.columns) == {
            "dc_entry_upper",
            "dc_entry_lower",
            "dc_exit_lower",
            "breakout_up",
            "first_breakout_up",
            "exit_long",
        }

    def test_no_breakout_before_channel_is_complete(self) -> None:
        candles = make_candles([100.0 + float(i) for i in range(30)])

        frame = donchian_breakout_frame(
            candles["high"], candles["low"], candles["close"], entry_period=20
        )

        assert not frame["breakout_up"].iloc[:20].any()

    def test_does_not_mutate_inputs(self) -> None:
        candles = make_candles([100.0 + float(i) for i in range(30)])
        original = candles.copy(deep=True)

        donchian_breakout_frame(candles["high"], candles["low"], candles["close"])

        pd.testing.assert_frame_equal(candles, original)


class TestTurtleSignals:
    """Entry and exit rules."""

    def test_single_entry_per_breakout_episode(self, trending_breakout_candles) -> None:
        candles = trending_breakout_candles

        signals = turtle_entry_signals(candles["high"], candles["low"], candles["close"])

        assert int(signals.sum()) == 1

    def test_a_high_without_a_close_breakout_is_not_an_entry(self) -> None:
        closes = [100.0] * 30
        candles = make_candles(closes)
        candles.loc[candles.index[-1], "high"] = 500.0
        candles.loc[candles.index[-1], "close"] = 100.0

        signals = turtle_entry_signals(candles["high"], candles["low"], candles["close"])

        assert not signals.any()

    def test_flat_market_produces_no_entries(self) -> None:
        candles = make_candles([100.0] * 40)

        signals = turtle_entry_signals(candles["high"], candles["low"], candles["close"])

        assert not signals.any()

    def test_selloff_produces_exit_signals(self, breakdown_candles) -> None:
        candles = breakdown_candles

        signals = turtle_exit_signals(candles["high"], candles["low"], candles["close"])

        assert signals.iloc[len(candles) // 2 :].any()

    def test_signals_are_prefix_invariant(self, trending_breakout_candles) -> None:
        candles = trending_breakout_candles
        cut = 45

        full = turtle_entry_signals(candles["high"], candles["low"], candles["close"])
        truncated = turtle_entry_signals(
            candles["high"].iloc[:cut],
            candles["low"].iloc[:cut],
            candles["close"].iloc[:cut],
        )

        assert full.iloc[:cut].tolist() == truncated.tolist()

    def test_rejects_zero_period(self) -> None:
        candles = make_candles([100.0] * 30)

        with pytest.raises(ValueError):
            turtle_entry_signals(candles["high"], candles["low"], candles["close"], entry_period=0)
