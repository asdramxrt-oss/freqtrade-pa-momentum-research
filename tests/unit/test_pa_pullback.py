"""Unit tests for the pullback-continuation setup.

The scenarios are deterministic synthetic candle series: a flat base, a
directional impulse, a controlled pullback and a continuation bar. No market data
is downloaded.
"""

from __future__ import annotations

import numpy as np
import pytest
from pa_pullback import pullback_continuation_frame

from tests.helpers import make_candles

LONG_BASE = [100.0] * 12
LONG_IMPULSE = [104.0, 108.0, 112.0, 116.0, 120.0, 124.0, 128.0, 132.0, 136.0, 140.0]
LONG_PULLBACK = [138.0, 135.0, 132.0, 131.0, 133.0]
LONG_CONFIRM = [137.0]


def _frame(closes: list[float]):
    """
    Build the setup frame for a synthetic close series.

    :param closes: Close prices.
    :return: Setup frame with ``date`` removed for compact assertions.
    """
    candles = make_candles(closes)
    frame = pullback_continuation_frame(
        candles["open"], candles["high"], candles["low"], candles["close"]
    )
    frame["date"] = candles["date"]
    return frame


def _mirror(closes: list[float], center: float = 200.0) -> list[float]:
    """
    Reflect a close series around ``center``.

    :param closes: Original closes.
    :param center: Reflection level.
    :return: Mirrored closes.
    """
    return [center - value for value in closes]


class TestLongSetup:
    """Impulse, pullback, structure and confirmation for longs."""

    def test_produces_at_least_one_long_signal(self) -> None:
        frame = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)

        assert int(frame["long_signal"].sum()) >= 1

    def test_signal_bar_satisfies_every_rule_predicate(self) -> None:
        frame = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)
        signal_index = frame.index[frame["long_signal"]].tolist()[0]

        row = frame.loc[signal_index]
        assert row["impulse_atr_long"] >= 3.0
        assert 0.5 <= row["pullback_depth_atr_long"] <= 2.0
        assert 1 <= row["pullback_bars_long"] <= 10
        assert row["dist_from_structure_atr_long"] > 0
        assert frame["last_swing_high"].loc[signal_index] > frame["origin_low"].loc[signal_index]

    def test_no_signal_before_confirmation(self) -> None:
        frame = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK)
        setup_end = len(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK)

        assert int(frame["long_signal"].iloc[:setup_end].sum()) == 0

    def test_structure_break_prevents_signal(self) -> None:
        # A pullback that gives back the entire impulse violates the origin low.
        deep_pullback = [130.0, 118.0, 106.0, 96.0, 90.0]
        frame = _frame(LONG_BASE + LONG_IMPULSE + deep_pullback + [95.0])

        assert int(frame["long_signal"].sum()) == 0

    def test_no_pullback_prevents_signal(self) -> None:
        # Price never retraces, so depth is below the minimum.
        continuation = [144.0, 148.0, 152.0]
        frame = _frame(LONG_BASE + LONG_IMPULSE + continuation)

        assert int(frame["long_signal"].sum()) == 0

    def test_recency_bound_is_enforced(self) -> None:
        # A very long, drifting pullback exceeds max_pullback_bars.
        slow_pullback = [138.0] * 20
        frame = _frame(LONG_BASE + LONG_IMPULSE + slow_pullback + [137.0])

        assert int(frame["long_signal"].sum()) == 0

    def test_one_signal_per_episode_despite_persistent_confirmation(self) -> None:
        persistent = [137.0, 139.0, 141.0, 143.0]
        frame = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + persistent)

        assert int(frame["long_signal"].sum()) == 1


class TestShortSetup:
    """The short side must be an exact mirror of the long side."""

    def test_mirrored_series_produces_a_short_signal(self) -> None:
        mirrored = _mirror(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)
        frame = _frame(mirrored)

        assert int(frame["short_signal"].sum()) >= 1

    def test_mirrored_series_produces_no_long_signal(self) -> None:
        mirrored = _mirror(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)
        frame = _frame(mirrored)

        assert int(frame["long_signal"].sum()) == 0

    def test_short_signal_bar_satisfies_predicates(self) -> None:
        mirrored = _mirror(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)
        frame = _frame(mirrored)
        signal_index = frame.index[frame["short_signal"]].tolist()[0]

        row = frame.loc[signal_index]
        assert row["impulse_atr_short"] >= 3.0
        assert 0.5 <= row["pullback_depth_atr_short"] <= 2.0
        assert frame["origin_high"].loc[signal_index] > frame["last_swing_low"].loc[signal_index]

    def test_long_and_short_are_mutually_exclusive_on_clean_scenarios(self) -> None:
        up = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)
        down = _frame(_mirror(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM))

        assert not ((up["long_signal"]) & (up["short_signal"])).any()
        assert not ((down["long_signal"]) & (down["short_signal"])).any()


class TestCausality:
    """Signals and geometry computed on truncated data must not change."""

    def test_signals_are_prefix_invariant(self) -> None:
        closes = LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM
        cut = len(closes) - 3

        full = _frame(closes)
        truncated = _frame(closes[:cut])

        assert full["long_signal"].iloc[:cut].tolist() == truncated["long_signal"].tolist()
        assert full["short_signal"].iloc[:cut].tolist() == truncated["short_signal"].tolist()

    @pytest.mark.parametrize(
        "column",
        [
            "impulse_atr_long",
            "pullback_depth_atr_long",
            "pullback_bars_long",
            "dist_from_structure_atr_long",
            "last_swing_high",
            "origin_low",
        ],
    )
    def test_geometry_is_prefix_invariant(self, column: str) -> None:
        closes = LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM
        cut = len(closes) - 3

        full = _frame(closes)[column].iloc[:cut]
        truncated = _frame(closes[:cut])[column]

        full_values = np.asarray(full, dtype=float)
        truncated_values = np.asarray(truncated, dtype=float)
        assert (np.isnan(full_values) == np.isnan(truncated_values)).all()
        finite = ~np.isnan(full_values)
        assert full_values[finite].tolist() == pytest.approx(truncated_values[finite].tolist())


class TestEdgeCases:
    """Short series, NaN handling and column contract."""

    def test_short_series_emits_no_signals_and_does_not_raise(self) -> None:
        frame = _frame([100.0] * 4)

        assert int(frame["long_signal"].sum()) == 0
        assert int(frame["short_signal"].sum()) == 0

    def test_signal_columns_are_boolean(self) -> None:
        frame = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)

        for column in ("long_signal", "short_signal", "exit_long_signal", "exit_short_signal"):
            assert set(frame[column].unique()) <= {True, False}

    def test_expected_columns_are_present(self) -> None:
        frame = _frame(LONG_BASE + LONG_IMPULSE + LONG_PULLBACK + LONG_CONFIRM)

        for column in (
            "atr",
            "long_signal",
            "short_signal",
            "impulse_atr_long",
            "impulse_atr_short",
            "pullback_depth_atr_long",
            "pullback_depth_atr_short",
            "pullback_bars_long",
            "pullback_bars_short",
            "dist_from_structure_atr_long",
            "dist_from_structure_atr_short",
            "trigger_margin_atr_long",
            "trigger_margin_atr_short",
        ):
            assert column in frame.columns
