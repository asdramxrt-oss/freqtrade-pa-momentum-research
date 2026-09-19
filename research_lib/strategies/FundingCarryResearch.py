"""P3-EXP-003 research strategy: perpetual funding carry (single-leg).

RESEARCH ONLY, outside `user_data/strategies/`. The production strategy is not
imported or modified.

Frozen definition (specification §6.1):
* Signal      : sign of the trailing 3-day mean funding rate, per pair.
* Position    : the funding-RECEIVING side only.
                mean funding > 0  -> SHORT (longs pay shorts)
                mean funding < 0  -> LONG  (shorts pay longs)
* Rebalance   : once per day (at the 00:00 UTC 4h bar); flip when the sign flips.
* Sizing      : equal notional per active pair = 10% of current equity
                (so 10 positions = 1x gross exposure cap).
* No threshold on |funding|.

The engine applies funding PnL to held futures positions from the real
`funding_rate` data; the strategy only chooses the side.

Risk note: this engine intentionally has **no directional stop**, because the
frozen specification defines the exit as the funding-sign flip. The stoploss
value is set to an extreme backstop (-99%) purely to satisfy the framework; it is
not part of the strategy logic. This is recorded as a limitation.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame

_SHARED_DIR = Path(__file__).resolve().parents[2] / "user_data" / "strategies" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from freqtrade.strategy import IStrategy  # noqa: E402
from pa_signals import rising_edge  # noqa: E402


class FundingCarry(IStrategy):
    """Single-leg perpetual funding-harvest research strategy."""

    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = True
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    position_adjustment_enable = False

    minimal_roi: dict = {}
    # Extreme backstop only; the real exit is the funding-sign flip.
    stoploss = -0.99
    use_custom_stoploss = False

    # Frozen parameters (specification §6.1).
    funding_timeframe: str = "1h"
    lookback_days: int = 3
    stake_fraction: float = 0.10

    @property
    def startup_candle_count(self) -> int:
        """
        Warm-up bars so the trailing funding mean exists.

        :return: Number of warm-up candles.
        """
        return (self.lookback_days * 24 // 4) + 6

    def _funding_mean(self, pair: str, dates: pd.Series) -> pd.Series:
        """
        Causal trailing mean funding aligned to the candle dates.

        :param pair: Pair.
        :param dates: Candle ``date`` series (tz-aware UTC).
        :return: Series of trailing mean funding, NaN where unavailable.
        """
        try:
            funding = self.dp.get_pair_dataframe(
                pair, self.funding_timeframe, candle_type="funding_rate"
            )
        except Exception:  # pragma: no cover - runtime dependent
            return pd.Series(np.nan, index=dates.index)
        if funding is None or funding.empty or "funding_rate" not in funding.columns:
            return pd.Series(np.nan, index=dates.index)

        frame = funding.loc[:, ["date", "funding_rate"]].dropna().sort_values("date")
        frame = frame.set_index("date")
        frame["mean3d"] = (
            frame["funding_rate"].rolling(f"{self.lookback_days}D", min_periods=1).mean()
        )
        frame = frame.reset_index()
        left = pd.DataFrame({"date": pd.to_datetime(dates, utc=True).to_numpy()}).sort_values(
            "date"
        )
        merged = pd.merge_asof(
            left, frame.loc[:, ["date", "mean3d"]], on="date", direction="backward"
        )
        merged = merged.sort_index()
        return pd.Series(merged["mean3d"].to_numpy(), index=dates.index)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Attach the trailing funding mean (causal).

        :param dataframe: Candle data.
        :param metadata: Freqtrade metadata.
        :return: Enriched frame.
        """
        dataframe["funding_mean3d"] = self._funding_mean(metadata["pair"], dataframe["date"])
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter the funding-receiving side on the daily rebalance bar.

        :param dataframe: Indicator frame.
        :param metadata: Freqtrade metadata.
        :return: Frame with entry columns.
        """
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        is_daily = pd.to_datetime(dataframe["date"], utc=True).dt.hour % 24 == 0
        mean = dataframe["funding_mean3d"]
        target_long = (mean < 0).fillna(False)
        target_short = (mean > 0).fillna(False)

        enter_long = rising_edge(target_long) & is_daily
        enter_short = rising_edge(target_short) & is_daily
        dataframe.loc[enter_long, "enter_long"] = 1
        dataframe.loc[enter_long, "enter_tag"] = "carry_long"
        dataframe.loc[enter_short, "enter_short"] = 1
        dataframe.loc[enter_short, "enter_tag"] = "carry_short"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit when the funding sign flips (the opposite side becomes the receiver).

        :param dataframe: Indicator frame.
        :param metadata: Freqtrade metadata.
        :return: Frame with exit columns.
        """
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        is_daily = pd.to_datetime(dataframe["date"], utc=True).dt.hour % 24 == 0
        mean = dataframe["funding_mean3d"]
        target_long = (mean < 0).fillna(False)
        target_short = (mean > 0).fillna(False)

        exit_long = rising_edge(target_short) & is_daily
        exit_short = rising_edge(target_long) & is_daily
        dataframe.loc[exit_long, "exit_long"] = 1
        dataframe.loc[exit_short, "exit_short"] = 1
        dataframe.loc[exit_long | exit_short, "exit_tag"] = "carry_flip"
        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        """
        Equal notional per active pair: ``stake_fraction`` of current equity.

        :param pair: Pair being entered.
        :param current_time: Current time.
        :param current_rate: Current rate.
        :param proposed_stake: Freqtrade default stake.
        :param min_stake: Exchange minimum.
        :param max_stake: Maximum allowed.
        :param leverage: Leverage (1.0).
        :param entry_tag: Entry tag.
        :param side: "long" or "short".
        :return: Stake in quote currency.
        """
        try:
            equity = float(self.wallets.get_total_stake_amount())
        except Exception:  # pragma: no cover - runtime dependent
            equity = proposed_stake
        equity = equity if equity > 0 else proposed_stake
        stake = min(equity * self.stake_fraction, max_stake)
        if min_stake is not None and stake < min_stake:
            return 0.0
        return stake
