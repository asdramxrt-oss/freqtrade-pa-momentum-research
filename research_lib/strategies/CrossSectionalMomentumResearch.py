"""P3-EXP-004A research strategy: cross-sectional momentum.

RESEARCH ONLY, outside `user_data/strategies/`. The production strategy is not
imported or modified.

Frozen definition (specification §6.2):
* Signal    : rank the fixed 10-pair universe by trailing 30-day return.
* Position  : long top 3, short bottom 3.
* Rebalance : every 7 days at a fixed bar.
* Sizing    : equal notional per active pair.

This implementation uses the 00:00 UTC Monday 4h candle as the fixed weekly
rebalance bar. It performs no parameter search and does not select pairs.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class CrossSectionalMomentum(IStrategy):
    """Long top-3 / short bottom-3 cross-sectional momentum research engine."""

    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = True
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    position_adjustment_enable = False

    minimal_roi: dict = {}
    # Research engine exits at weekly rebalance; this is only a framework backstop.
    stoploss = -0.99
    use_custom_stoploss = False

    lookback_days: int = 30
    top_n: int = 3
    bottom_n: int = 3
    stake_fraction: float = 1.0 / 6.0

    @property
    def startup_candle_count(self) -> int:
        """Warm-up bars so the 30-day momentum value exists."""
        return (self.lookback_days * 24 // 4) + 6

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Attach the current pair's trailing return and cross-sectional side."""
        pair = metadata["pair"]
        dates = pd.to_datetime(dataframe["date"], utc=True)
        dataframe["xsmom_return_30d"] = self._trailing_return(dataframe["close"])
        target_side = self._target_side(pair, dates)
        dataframe["xsmom_target_side"] = target_side.to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Enter the selected side only on the fixed weekly rebalance bar."""
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        rebalance = self._is_rebalance_bar(dataframe["date"])
        long_target = dataframe["xsmom_target_side"] == 1
        short_target = dataframe["xsmom_target_side"] == -1

        dataframe.loc[rebalance & long_target, "enter_long"] = 1
        dataframe.loc[rebalance & long_target, "enter_tag"] = "xsmom_top3"
        dataframe.loc[rebalance & short_target, "enter_short"] = 1
        dataframe.loc[rebalance & short_target, "enter_tag"] = "xsmom_bottom3"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Exit at rebalance when the pair is no longer selected for that side."""
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        rebalance = self._is_rebalance_bar(dataframe["date"])
        long_target = dataframe["xsmom_target_side"] == 1
        short_target = dataframe["xsmom_target_side"] == -1

        dataframe.loc[rebalance & ~long_target, "exit_long"] = 1
        dataframe.loc[rebalance & ~short_target, "exit_short"] = 1
        dataframe.loc[rebalance, "exit_tag"] = "xsmom_weekly_rebalance"
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
        """Equal notional per active leg, capped by exchange/framework limits."""
        try:
            equity = float(self.wallets.get_total_stake_amount())
        except Exception:  # pragma: no cover - runtime dependent
            equity = proposed_stake * 6.0
        equity = equity if equity > 0 else proposed_stake * 6.0
        stake = min(equity * self.stake_fraction, max_stake)
        if min_stake is not None and stake < min_stake:
            return 0.0
        return stake

    def _target_side(self, pair: str, dates: pd.Series) -> pd.Series:
        """Return 1 for top-3, -1 for bottom-3, 0 otherwise for each date."""
        universe = self._whitelist()
        if pair not in universe:
            universe = [*universe, pair]

        momentum_by_pair = {
            candidate: self._momentum_for_pair(candidate, dates) for candidate in universe
        }
        frame = pd.DataFrame(momentum_by_pair, index=dates.index)
        target = pd.Series(0, index=dates.index, dtype=int)

        valid_counts = frame.notna().sum(axis=1)
        enough_pairs = valid_counts >= self.top_n + self.bottom_n
        ranks_high = frame.rank(axis=1, method="first", ascending=False)
        ranks_low = frame.rank(axis=1, method="first", ascending=True)

        target.loc[enough_pairs & (ranks_high[pair] <= self.top_n)] = 1
        target.loc[enough_pairs & (ranks_low[pair] <= self.bottom_n)] = -1
        return target

    def _momentum_for_pair(self, pair: str, dates: pd.Series) -> pd.Series:
        """Causal 30-day return for a pair, aligned to the current dataframe."""
        try:
            frame = self.dp.get_pair_dataframe(pair, self.timeframe)
        except Exception:  # pragma: no cover - runtime dependent
            return pd.Series(np.nan, index=dates.index)
        if frame is None or frame.empty or "date" not in frame.columns or "close" not in frame:
            return pd.Series(np.nan, index=dates.index)

        source = frame.loc[:, ["date", "close"]].copy()
        source["date"] = pd.to_datetime(source["date"], utc=True)
        source = source.sort_values("date")
        source["momentum"] = self._trailing_return(source["close"])
        left = pd.DataFrame({"date": dates.to_numpy()}).sort_values("date")
        merged = pd.merge_asof(
            left,
            source.loc[:, ["date", "momentum"]],
            on="date",
            direction="backward",
        )
        merged = merged.sort_index()
        return pd.Series(merged["momentum"].to_numpy(), index=dates.index)

    def _whitelist(self) -> list[str]:
        """Best-effort fixed universe from the runtime config."""
        try:
            pairs = self.dp.current_whitelist()
        except Exception:  # pragma: no cover - runtime dependent
            pairs = None
        if pairs:
            return list(pairs)
        return list(self.config.get("exchange", {}).get("pair_whitelist", []))

    def _trailing_return(self, close: pd.Series) -> pd.Series:
        """Trailing 30-day return on 4h candles."""
        periods = self.lookback_days * 24 // 4
        return close.astype(float).pct_change(periods=periods)

    @staticmethod
    def _is_rebalance_bar(dates: pd.Series) -> pd.Series:
        """Monday 00:00 UTC is the fixed weekly rebalance bar."""
        stamps = pd.to_datetime(dates, utc=True)
        return (stamps.dt.weekday == 0) & (stamps.dt.hour == 0)
