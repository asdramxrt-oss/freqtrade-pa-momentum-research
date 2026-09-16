"""Tests for the Turtle/Donchian baseline strategy (EXP-001).

These tests exercise the strategy object directly rather than running a
backtest, so they are fast, deterministic and require no market data. The point
is to pin down the specification: fixed parameters, causal signals, one entry
per breakout episode, and ATR-consistent risk behaviour.
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
STRATEGY_FILE = PROJECT_ROOT / "user_data" / "strategies" / "turtle" / "DonchianTurtleBaseline.py"


def _load_strategy_module():
    """
    Load the strategy file the way a research script would.

    :return: The imported strategy module.
    """
    spec = importlib.util.spec_from_file_location("DonchianTurtleBaseline", STRATEGY_FILE)
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
def strategy(strategy_module):
    """
    A fresh strategy instance with an empty config.

    :return: Strategy instance.
    """
    return strategy_module.DonchianTurtleBaseline({})


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
    """Minimal Trade stand-in with custom-data storage."""

    def __init__(self, open_rate: float, open_date: datetime) -> None:
        self.open_rate = open_rate
        self.open_date_utc = open_date
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


def _analysed(strategy, candles: pd.DataFrame) -> pd.DataFrame:
    """
    Run indicators and signals over a candle frame.

    :param strategy: Strategy instance.
    :param candles: Raw OHLCV frame.
    :return: Enriched frame.
    """
    frame = strategy.populate_indicators(candles.copy(), {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})


class TestSpecification:
    """The baseline specification must not drift."""

    def test_classic_turtle_parameters_are_fixed(self, strategy) -> None:
        assert strategy.entry_period == 20
        assert strategy.exit_period == 10
        assert strategy.atr_period == 20

    def test_risk_parameters_are_fixed(self, strategy) -> None:
        assert strategy.atr_stop_multiple == pytest.approx(2.0)
        assert strategy.risk_per_trade == pytest.approx(0.01)

    def test_is_long_only_and_not_pyramiding(self, strategy) -> None:
        assert strategy.can_short is False
        assert strategy.position_adjustment_enable is False

    def test_roi_is_disabled(self, strategy) -> None:
        assert strategy.minimal_roi == {}

    def test_startup_candles_cover_warmup(self, strategy) -> None:
        assert strategy.startup_candle_count == 30

    def test_timeframe_is_declared(self, strategy) -> None:
        assert strategy.timeframe == "4h"


class TestIndicators:
    """Indicator population."""

    def test_adds_expected_columns(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])

        frame = strategy.populate_indicators(candles, {"pair": "BTC/USDT"})

        for column in ("dc_entry_upper", "dc_entry_lower", "dc_exit_lower", "atr", "atr_pct"):
            assert column in frame.columns

    def test_channel_is_nan_during_warmup(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])

        frame = strategy.populate_indicators(candles, {"pair": "BTC/USDT"})

        assert frame["dc_entry_upper"].iloc[: strategy.entry_period - 1].isna().all()
        assert frame["dc_entry_upper"].iloc[strategy.entry_period :].notna().all()

    def test_atr_matches_independent_calculation(self, strategy) -> None:
        candles = make_candles([100.0 + float(i % 7) for i in range(80)])

        frame = strategy.populate_indicators(candles, {"pair": "BTC/USDT"})

        from pa_indicators import atr

        expected = atr(candles["high"], candles["low"], candles["close"], 20)
        assert frame["atr"].tolist()[20:] == pytest.approx(expected.tolist()[20:])


class TestSignals:
    """Entry and exit signals."""

    def test_one_entry_per_breakout_episode(self, strategy, trending_breakout_candles) -> None:
        frame = _analysed(strategy, trending_breakout_candles)

        assert int(frame["enter_long"].sum()) == 1
        assert frame.loc[frame["enter_long"] == 1, "enter_tag"].iloc[0] == "donchian_breakout"

    def test_entries_require_a_breakout(self, strategy) -> None:
        frame = _analysed(strategy, make_candles([100.0] * 60))

        assert int(frame["enter_long"].sum()) == 0

    def test_no_entry_while_atr_is_nan(self, strategy, trending_breakout_candles) -> None:
        frame = _analysed(strategy, trending_breakout_candles)
        warmup = frame.iloc[: strategy.startup_candle_count]

        assert int(warmup["enter_long"].sum()) == 0

    def test_exit_fires_on_selloff(self, strategy, breakdown_candles) -> None:
        frame = _analysed(strategy, breakdown_candles)

        assert int(frame["exit_long"].sum()) >= 1
        assert frame.loc[frame["exit_long"] == 1, "exit_tag"].iloc[0] == "donchian_exit"

    def test_entries_and_exits_are_mutually_exclusive(
        self, strategy, trending_breakout_candles
    ) -> None:
        frame = _analysed(strategy, trending_breakout_candles)

        assert not ((frame["enter_long"] == 1) & (frame["exit_long"] == 1)).any()

    def test_signals_are_prefix_invariant(self, strategy, trending_breakout_candles) -> None:
        cut = 45
        full = _analysed(strategy, trending_breakout_candles)
        truncated = _analysed(strategy, trending_breakout_candles.iloc[:cut].copy())

        assert full["enter_long"].iloc[:cut].tolist() == truncated["enter_long"].tolist()
        assert full["exit_long"].iloc[:cut].tolist() == truncated["exit_long"].tolist()

    def test_signal_columns_are_integers(self, strategy, trending_breakout_candles) -> None:
        frame = _analysed(strategy, trending_breakout_candles)

        assert set(frame["enter_long"].unique()) <= {0, 1}
        assert set(frame["exit_long"].unique()) <= {0, 1}


class TestStoploss:
    """Fixed ATR stop derived from entry-time ATR."""

    def test_returns_two_atr_stop_below_entry(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])
        frame = _analysed(strategy, candles)
        entry_rate = float(frame["close"].iloc[-1])
        entry_time = frame["date"].iloc[-1]
        atr_at_entry = float(frame["atr"].iloc[-1])

        strategy.dp = _FakeDp(frame)
        trade = _FakeTrade(entry_rate, entry_time)

        ratio = strategy.custom_stoploss("BTC/USDT", trade, entry_time, entry_rate, 0.0, False)

        stop_price = entry_rate - atr_stop_distance(atr_at_entry, strategy.atr_stop_multiple)
        assert ratio == pytest.approx((stop_price - entry_rate) / entry_rate)

    def test_caches_entry_atr_on_trade(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])
        frame = _analysed(strategy, candles)
        strategy.dp = _FakeDp(frame)
        trade = _FakeTrade(float(frame["close"].iloc[-1]), frame["date"].iloc[-1])

        strategy.custom_stoploss(
            "BTC/USDT", trade, frame["date"].iloc[-1], float(frame["close"].iloc[-1]), 0.0, False
        )

        assert trade.get_custom_data("atr_entry") == pytest.approx(float(frame["atr"].iloc[-1]))

    def test_returns_none_without_data(self, strategy) -> None:
        strategy.dp = _FakeDp(None)
        trade = _FakeTrade(100.0, datetime(2024, 1, 1, tzinfo=None))

        assert strategy.custom_stoploss("BTC/USDT", trade, None, 100.0, 0.0, False) is None

    def test_stop_is_wider_when_volatility_is_higher(self, strategy) -> None:
        calm = make_candles([100.0 + 0.1 * float(i % 3) for i in range(60)])
        wild = make_candles([100.0 + 10.0 * float((-1) ** i) for i in range(60)])

        calm_frame = _analysed(strategy, calm)
        wild_frame = _analysed(strategy, wild)

        strategy.dp = _FakeDp(calm_frame)
        calm_ratio = strategy.custom_stoploss(
            "BTC/USDT",
            _FakeTrade(float(calm_frame["close"].iloc[-1]), calm_frame["date"].iloc[-1]),
            calm_frame["date"].iloc[-1],
            float(calm_frame["close"].iloc[-1]),
            0.0,
            False,
        )

        strategy.dp = _FakeDp(wild_frame)
        wild_ratio = strategy.custom_stoploss(
            "BTC/USDT",
            _FakeTrade(float(wild_frame["close"].iloc[-1]), wild_frame["date"].iloc[-1]),
            wild_frame["date"].iloc[-1],
            float(wild_frame["close"].iloc[-1]),
            0.0,
            False,
        )

        assert wild_ratio < calm_ratio


class TestStakeSizing:
    """Risk-scaled position sizing."""

    def test_falls_back_to_proposed_stake_without_data(self, strategy) -> None:
        strategy.dp = _FakeDp(None)

        stake = strategy.custom_stake_amount(
            "BTC/USDT", None, 100.0, 1000.0, None, 1e9, 1.0, "donchian_breakout", "long"
        )

        assert stake == pytest.approx(1000.0)

    def test_scales_stake_down_as_atr_grows(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])
        frame = _analysed(strategy, candles)
        current_time = frame["date"].iloc[-1]
        current_rate = float(frame["close"].iloc[-1])
        atr_at_entry = float(frame["atr"].iloc[-1])

        strategy.dp = _FakeDp(frame)
        stake = strategy.custom_stake_amount(
            "BTC/USDT", current_time, current_rate, 10_000.0, None, 1e9, 1.0, None, "long"
        )

        expected = risk_based_stake(
            equity=10_000.0,
            risk_per_trade=strategy.risk_per_trade,
            stop_distance=atr_stop_distance(atr_at_entry, strategy.atr_stop_multiple),
            price=current_rate,
            max_stake_fraction=strategy.max_stake_fraction,
        )
        assert stake == pytest.approx(expected)

    def test_returns_zero_below_exchange_minimum(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])
        frame = _analysed(strategy, candles)

        strategy.dp = _FakeDp(frame)
        stake = strategy.custom_stake_amount(
            "BTC/USDT",
            frame["date"].iloc[-1],
            float(frame["close"].iloc[-1]),
            1e-12,
            None,
            1e9,
            1.0,
            None,
            "long",
        )

        assert stake >= 0.0

    def test_stake_is_non_negative(self, strategy) -> None:
        candles = make_candles([100.0 + float(i) for i in range(60)])
        frame = _analysed(strategy, candles)
        strategy.dp = _FakeDp(frame)

        stake = strategy.custom_stake_amount(
            "BTC/USDT",
            frame["date"].iloc[-1],
            float(frame["close"].iloc[-1]),
            5_000.0,
            100.0,
            1e9,
            1.0,
            None,
            "long",
        )

        assert stake == 0.0 or stake >= 100.0
