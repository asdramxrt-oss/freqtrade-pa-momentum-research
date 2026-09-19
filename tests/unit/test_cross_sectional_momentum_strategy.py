"""Tests for the P3-EXP-004A cross-sectional momentum research strategy."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

from tests.helpers import make_candles  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_FILE = PROJECT_ROOT / "research_lib" / "strategies" / "CrossSectionalMomentumResearch.py"
PAIRS = [
    "BTC/USDT:USDT",
    "ETH/USDT:USDT",
    "BNB/USDT:USDT",
    "SOL/USDT:USDT",
    "XRP/USDT:USDT",
    "ADA/USDT:USDT",
    "DOGE/USDT:USDT",
    "LINK/USDT:USDT",
    "AVAX/USDT:USDT",
    "DOT/USDT:USDT",
]


def _load_strategy_module():
    class _IStrategy:
        def __init__(self, config=None) -> None:
            self.config = config or {}

    freqtrade = types.ModuleType("freqtrade")
    strategy = types.ModuleType("freqtrade.strategy")
    strategy.IStrategy = _IStrategy
    sys.modules["freqtrade"] = freqtrade
    sys.modules["freqtrade.strategy"] = strategy

    spec = importlib.util.spec_from_file_location("CrossSectionalMomentumResearch", STRATEGY_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeDp:
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self._frames = frames

    def current_whitelist(self):
        return list(self._frames)

    def get_pair_dataframe(self, pair: str, timeframe: str):
        return self._frames[pair]


@pytest.fixture(scope="module")
def strategy_module():
    return _load_strategy_module()


@pytest.fixture
def strategy(strategy_module):
    bot = strategy_module.CrossSectionalMomentum({"exchange": {"pair_whitelist": PAIRS}})
    frames = {}
    for index, pair in enumerate(PAIRS):
        drift = 0.05 - (index * 0.01)
        closes = [100.0 * (1.0 + drift * step / 220.0) for step in range(220)]
        frames[pair] = make_candles(closes, start="2024-01-01")
    bot.dp = _FakeDp(frames)
    return bot


def _analysed(strategy, pair: str) -> pd.DataFrame:
    frame = strategy.dp.get_pair_dataframe(pair, strategy.timeframe).copy()
    frame = strategy.populate_indicators(frame, {"pair": pair})
    frame = strategy.populate_entry_trend(frame, {"pair": pair})
    return strategy.populate_exit_trend(frame, {"pair": pair})


def test_specification_parameters_are_fixed(strategy) -> None:
    assert strategy.lookback_days == 30
    assert strategy.top_n == 3
    assert strategy.bottom_n == 3
    assert strategy.can_short is True
    assert strategy.position_adjustment_enable is False
    assert strategy.timeframe == "4h"


def test_ranks_top_three_long_and_bottom_three_short(strategy) -> None:
    top = _analysed(strategy, PAIRS[0])
    middle = _analysed(strategy, PAIRS[4])
    bottom = _analysed(strategy, PAIRS[-1])

    assert top["xsmom_target_side"].iloc[-1] == 1
    assert middle["xsmom_target_side"].iloc[-1] == 0
    assert bottom["xsmom_target_side"].iloc[-1] == -1


def test_entries_only_on_monday_midnight_rebalance(strategy) -> None:
    frame = _analysed(strategy, PAIRS[0])
    entries = frame.loc[frame["enter_long"] == 1, "date"]

    assert not entries.empty
    assert (pd.to_datetime(entries, utc=True).dt.weekday == 0).all()
    assert (pd.to_datetime(entries, utc=True).dt.hour == 0).all()


def test_equal_notional_stake_fraction(strategy) -> None:
    class _Wallets:
        @staticmethod
        def get_total_stake_amount() -> float:
            return 12000.0

    strategy.wallets = _Wallets()

    stake = strategy.custom_stake_amount(
        PAIRS[0], None, 100.0, 1000.0, None, 100000.0, 1.0, "xsmom_top3", "long"
    )

    assert stake == pytest.approx(2000.0)
