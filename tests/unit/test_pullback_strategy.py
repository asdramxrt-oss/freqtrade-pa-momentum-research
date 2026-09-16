"""Tests for the pullback-continuation strategy (EXP-003).

These tests pin the specification: fixed parameters, direction scope, causal
signals, one entry per episode, symmetric long/short stops and risk-scaled sizing.
They exercise the strategy object directly and never run a backtest.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("freqtrade", reason="freqtrade must be importable")

from pa_risk import atr_stop_distance, risk_based_stake  # noqa: E402

from tests.helpers import make_candles  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_FILE = PROJECT_ROOT / "user_data" / "strategies" / "pullback" / "PullbackContinuation.py"

LONG_CLOSES = (
    [100.0] * 12
    + [104.0, 108.0, 112.0, 116.0, 120.0, 124.0, 128.0, 132.0, 136.0, 140.0]
    + [138.0, 135.0, 132.0, 131.0, 133.0, 137.0]
)
MIRRORED_CLOSES = [200.0 - value for value in LONG_CLOSES]


def _load_strategy_module():
    """
    Load the strategy file the way a research script would.

    :return: The imported strategy module.
    """
    spec = importlib.util.spec_from_file_location("PullbackContinuation", STRATEGY_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def strategy_module():
    """
    Module-scoped import of the strategy under test.

    :return: The imported strategy module.
    """
    return _load_strategy_module()


@pytest.fixture
def combined(strategy_module):
    """Combined long+short strategy instance."""
    return strategy_module.PullbackContinuation({})


class _FakeDp:
    """Minimal DataProvider stand-in returning a pre-built dataframe."""

    def __init__(self, dataframe: pd.DataFrame | None) -> None:
        self._dataframe = dataframe

    def get_analyzed_dataframe(self, pair: str, timeframe: str):
        """
        Return the injected dataframe.

        :param pair: Ignored.
        :param timeframe: Ignored.
        :return: Tuple of (dataframe, last refreshed).
        """
        return self._dataframe, None


class _FakeTrade:
    """Minimal Trade stand-in with custom-data storage and a direction flag."""

    def __init__(self, open_rate: float, open_date: datetime, is_short: bool = False) -> None:
        self.open_rate = open_rate
        self.open_date_utc = open_date
        self.is_short = is_short
        self._custom_data: dict = {}

    def get_custom_data(self, key: str, default=None):
        """
        Read a stored value.

        :param key: Storage key.
        :param default: Value returned when the key is absent.
        :return: Stored value or ``default``.
        """
        return self._custom_data.get(key, default)

    def set_custom_data(self, key: str, value) -> None:
        """
        Store a value.

        :param key: Storage key.
        :param value: Value to store.
        """
        self._custom_data[key] = value


def _analysed(strategy, closes: list[float]) -> pd.DataFrame:
    """
    Run indicators, entries and exits over a synthetic close series.

    :param strategy: Strategy instance.
    :param closes: Close prices.
    :return: Enriched frame.
    """
    candles = make_candles(closes)
    frame = strategy.populate_indicators(candles.copy(), {"pair": "BTC/USDT:USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT:USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT:USDT"})


class TestSpecification:
    """The EXP-003 specification must not drift."""

    def test_pullback_parameters_are_fixed(self, combined) -> None:
        assert combined.swing_left == 2
        assert combined.swing_right == 2
        assert combined.atr_period == 20
        assert combined.impulse_min_atr == pytest.approx(3.0)
        assert combined.pullback_min_atr == pytest.approx(0.5)
        assert combined.pullback_max_atr == pytest.approx(2.0)
        assert combined.max_pullback_bars == 10
        assert combined.confirm_bars == 3

    def test_risk_parameters_are_fixed(self, combined) -> None:
        assert combined.atr_stop_multiple == pytest.approx(2.0)
        assert combined.risk_per_trade == pytest.approx(0.01)
        assert combined.position_adjustment_enable is False

    def test_direction_scope_per_class(self, strategy_module) -> None:
        assert strategy_module.PullbackContinuation.direction_scope == "both"
        assert strategy_module.PullbackContinuation.can_short is True
        assert strategy_module.PullbackContinuationLong.direction_scope == "long"
        assert strategy_module.PullbackContinuationLong.can_short is False
        assert strategy_module.PullbackContinuationShort.direction_scope == "short"
        assert strategy_module.PullbackContinuationShort.can_short is True

    def test_roi_is_disabled(self, combined) -> None:
        assert combined.minimal_roi == {}

    def test_timeframe_and_startup(self, combined) -> None:
        assert combined.timeframe == "4h"
        assert combined.startup_candle_count >= 30


class TestDirectionScope:
    """Direction scope must suppress the disallowed side, not the allowed one."""

    def test_long_only_emits_no_shorts(self, strategy_module) -> None:
        strategy = strategy_module.PullbackContinuationLong({})
        frame = _analysed(strategy, MIRRORED_CLOSES)

        assert int(frame["enter_short"].sum()) == 0

    def test_short_only_emits_no_longs(self, strategy_module) -> None:
        strategy = strategy_module.PullbackContinuationShort({})
        frame = _analysed(strategy, LONG_CLOSES)

        assert int(frame["enter_long"].sum()) == 0

    def test_combined_emits_long_on_upside_scenario(self, combined) -> None:
        frame = _analysed(combined, LONG_CLOSES)

        assert int(frame["enter_long"].sum()) >= 1
        assert int(frame["enter_short"].sum()) == 0

    def test_combined_emits_short_on_downside_scenario(self, combined) -> None:
        frame = _analysed(combined, MIRRORED_CLOSES)

        assert int(frame["enter_short"].sum()) >= 1
        assert int(frame["enter_long"].sum()) == 0


class TestSignals:
    """Entry/exit signal contract."""

    def test_entry_tags_are_direction_specific(self, combined) -> None:
        long_frame = _analysed(combined, LONG_CLOSES)
        short_frame = _analysed(combined, MIRRORED_CLOSES)

        assert (
            long_frame.loc[long_frame["enter_long"] == 1, "enter_tag"].iloc[0]
            == "pullback_continuation_long"
        )
        assert (
            short_frame.loc[short_frame["enter_short"] == 1, "enter_tag"].iloc[0]
            == "pullback_continuation_short"
        )

    def test_signal_columns_are_integers(self, combined) -> None:
        frame = _analysed(combined, LONG_CLOSES)

        for column in ("enter_long", "enter_short", "exit_long", "exit_short"):
            assert set(frame[column].unique()) <= {0, 1}

    def test_timestamp_alignment_is_preserved(self, combined) -> None:
        candles = make_candles(LONG_CLOSES)
        frame = _analysed(combined, LONG_CLOSES)

        assert frame["date"].tolist() == candles["date"].tolist()

    def test_signals_are_prefix_invariant(self, combined) -> None:
        cut = len(LONG_CLOSES) - 3
        full = _analysed(combined, LONG_CLOSES)
        truncated = _analysed(combined, LONG_CLOSES[:cut])

        assert full["enter_long"].iloc[:cut].tolist() == truncated["enter_long"].tolist()
        assert full["enter_short"].iloc[:cut].tolist() == truncated["enter_short"].tolist()

    def test_no_entry_while_atr_is_nan(self, combined) -> None:
        frame = _analysed(combined, LONG_CLOSES)
        nan_atr = frame["atr"].isna()

        assert int(frame.loc[nan_atr, "enter_long"].sum()) == 0
        assert int(frame.loc[nan_atr, "enter_short"].sum()) == 0

    def test_flat_market_produces_no_signals(self, combined) -> None:
        frame = _analysed(combined, [100.0] * 80)

        assert int(frame["enter_long"].sum()) == 0
        assert int(frame["enter_short"].sum()) == 0


class TestStoploss:
    """Symmetric fixed ATR stops."""

    def test_long_stop_is_below_entry(self, combined) -> None:
        frame = _analysed(combined, LONG_CLOSES)
        entry_rate = float(frame["close"].iloc[-1])
        entry_time = frame["date"].iloc[-1]
        atr_at_entry = float(frame["atr"].iloc[-1])

        combined.dp = _FakeDp(frame)
        trade = _FakeTrade(entry_rate, entry_time, is_short=False)

        ratio = combined.custom_stoploss("BTC/USDT:USDT", trade, entry_time, entry_rate, 0.0, False)

        stop_price = entry_rate - atr_stop_distance(atr_at_entry, combined.atr_stop_multiple)
        assert ratio < 0
        assert ratio == pytest.approx((stop_price - entry_rate) / entry_rate)

    def test_short_stop_is_above_entry(self, combined) -> None:
        frame = _analysed(combined, MIRRORED_CLOSES)
        entry_rate = float(frame["close"].iloc[-1])
        entry_time = frame["date"].iloc[-1]
        atr_at_entry = float(frame["atr"].iloc[-1])

        combined.dp = _FakeDp(frame)
        trade = _FakeTrade(entry_rate, entry_time, is_short=True)

        ratio = combined.custom_stoploss("BTC/USDT:USDT", trade, entry_time, entry_rate, 0.0, False)

        stop_price = entry_rate + atr_stop_distance(atr_at_entry, combined.atr_stop_multiple)
        assert ratio > 0
        assert ratio == pytest.approx((stop_price - entry_rate) / entry_rate)

    def test_returns_none_without_data(self, combined) -> None:
        combined.dp = _FakeDp(None)
        trade = _FakeTrade(100.0, datetime(2024, 1, 1), is_short=True)

        assert combined.custom_stoploss("BTC/USDT:USDT", trade, None, 100.0, 0.0, False) is None


class TestStakeSizing:
    """Risk-scaled sizing applies identically to both directions."""

    def test_scales_stake_from_atr_stop(self, combined) -> None:
        frame = _analysed(combined, LONG_CLOSES)
        current_time = frame["date"].iloc[-1]
        current_rate = float(frame["close"].iloc[-1])
        atr_at_entry = float(frame["atr"].iloc[-1])

        combined.dp = _FakeDp(frame)
        stake = combined.custom_stake_amount(
            "BTC/USDT:USDT", current_time, current_rate, 10_000.0, None, 1e9, 1.0, None, "short"
        )

        expected = risk_based_stake(
            equity=10_000.0,
            risk_per_trade=combined.risk_per_trade,
            stop_distance=atr_stop_distance(atr_at_entry, combined.atr_stop_multiple),
            price=current_rate,
            max_stake_fraction=combined.max_stake_fraction,
        )
        assert stake == pytest.approx(expected)

    def test_falls_back_without_data(self, combined) -> None:
        combined.dp = _FakeDp(None)

        stake = combined.custom_stake_amount(
            "BTC/USDT:USDT", None, 100.0, 1000.0, None, 1e9, 1.0, None, "long"
        )

        assert stake == pytest.approx(1000.0)


class TestNoTurtleCoupling:
    """EXP-003 must not reference Turtle signals."""

    def test_strategy_does_not_import_turtle(self) -> None:
        source = STRATEGY_FILE.read_text(encoding="utf-8")

        assert "DonchianTurtleBaseline" not in source
        assert "turtle" not in source.lower()
