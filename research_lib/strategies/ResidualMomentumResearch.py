"""P3-EXP-004B research strategy: residual momentum.

RESEARCH ONLY. Production strategy is not imported or modified.

Frozen definition (§6.3):
* Market benchmark: equal-weight universe return.
* Rolling OLS: r_i = alpha + beta * r_mkt + residual over 90 days.
* Regression uses information strictly before the ranking date.
* Signal: cumulative residual over 30 days.
* Long top 3 / short bottom 3.
* Weekly fixed-bar rebalance.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ResidualMomentum(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = True
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    position_adjustment_enable = False

    minimal_roi: dict = {}
    stoploss = -0.99
    use_custom_stoploss = False

    REGRESSION_DAYS = 90
    SIGNAL_DAYS = 30
    TOP_N = 3
    BOTTOM_N = 3
    STAKE_FRACTION = 1.0 / 6.0

    @property
    def startup_candle_count(self) -> int:
        # 90 days of 4h returns plus one extra bar for strict pre-ranking use.
        return self.REGRESSION_DAYS * 6 + self.SIGNAL_DAYS * 6 + 2

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]
        dates = pd.to_datetime(dataframe["date"], utc=True)
        signal_by_pair = self._residual_signal_for_pair(pair, dates)

        dataframe["resmom_residual_30d"] = signal_by_pair.to_numpy()
        dataframe["resmom_target_side"] = self._target_side(
            pair, dates, signal_by_pair
        ).to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0

        rebalance = self._is_rebalance_bar(dataframe["date"])
        long_target = dataframe["resmom_target_side"] == 1
        short_target = dataframe["resmom_target_side"] == -1

        dataframe.loc[rebalance & long_target, "enter_long"] = 1
        dataframe.loc[rebalance & long_target, "enter_tag"] = "resmom_top3"
        dataframe.loc[rebalance & short_target, "enter_short"] = 1
        dataframe.loc[rebalance & short_target, "enter_tag"] = "resmom_bottom3"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0

        rebalance = self._is_rebalance_bar(dataframe["date"])
        long_target = dataframe["resmom_target_side"] == 1
        short_target = dataframe["resmom_target_side"] == -1

        dataframe.loc[rebalance & ~long_target, "exit_long"] = 1
        dataframe.loc[rebalance & ~short_target, "exit_short"] = 1
        dataframe.loc[rebalance, "exit_tag"] = "resmom_weekly_rebalance"
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
        try:
            equity = float(self.wallets.get_total_stake_amount())
        except Exception:
            equity = proposed_stake * 6.0
        equity = equity if equity > 0 else proposed_stake * 6.0
        stake = min(equity * self.STAKE_FRACTION, max_stake)
        if min_stake is not None and stake < min_stake:
            return 0.0
        return stake

    def _whitelist(self) -> list[str]:
        try:
            pairs = self.dp.current_whitelist()
        except Exception:
            pairs = None
        if pairs:
            return list(pairs)
        return list(self.config.get("exchange", {}).get("pair_whitelist", []))

    def _pair_returns(self, pair: str) -> pd.DataFrame | None:
        try:
            frame = self.dp.get_pair_dataframe(pair, self.timeframe)
        except Exception:
            return None
        if frame is None or frame.empty or "date" not in frame or "close" not in frame:
            return None
        out = frame.loc[:, ["date", "close"]].copy()
        out["date"] = pd.to_datetime(out["date"], utc=True)
        out = out.sort_values("date").drop_duplicates("date")
        out["ret"] = out["close"].astype(float).pct_change()
        return out.loc[:, ["date", "ret"]]

    def _aligned_returns(self) -> pd.DataFrame | None:
        frames = {}
        for candidate in self._whitelist():
            frame = self._pair_returns(candidate)
            if frame is None:
                continue
            frames[candidate] = frame.set_index("date")["ret"]

        if len(frames) < self.TOP_N + self.BOTTOM_N:
            return None

        returns = pd.concat(frames, axis=1).sort_index()
        return returns

    def _residual_signal_for_pair(
        self, pair: str, dates: pd.Series
    ) -> pd.Series:
        returns = self._aligned_returns()
        if returns is None or pair not in returns.columns:
            return pd.Series(np.nan, index=dates.index)

        market = returns.mean(axis=1, skipna=True)
        y = returns[pair]
        valid = pd.concat({"y": y, "mkt": market}, axis=1).dropna()

        n_reg = self.REGRESSION_DAYS * 6
        n_signal = self.SIGNAL_DAYS * 6

        y_mean = valid["y"].rolling(n_reg, min_periods=n_reg).mean()
        x_mean = valid["mkt"].rolling(n_reg, min_periods=n_reg).mean()
        xy_mean = (valid["y"] * valid["mkt"]).rolling(
            n_reg, min_periods=n_reg
        ).mean()
        xx_mean = (valid["mkt"] * valid["mkt"]).rolling(
            n_reg, min_periods=n_reg
        ).mean()

        cov = xy_mean - x_mean * y_mean
        var = xx_mean - x_mean * x_mean
        beta = cov / var.replace(0.0, np.nan)
        alpha = y_mean - beta * x_mean
        residual = valid["y"] - alpha - beta * valid["mkt"]

        # Signal at ranking time uses only the residual history ending before it.
        signal = residual.rolling(
            n_signal, min_periods=n_signal
        ).sum().shift(1)

        source = signal.rename("signal").reset_index()
        left = pd.DataFrame({"date": pd.to_datetime(dates, utc=True)})
        merged = pd.merge_asof(
            left.sort_values("date"),
            source.sort_values("date"),
            on="date",
            direction="backward",
        )
        return pd.Series(merged["signal"].to_numpy(), index=dates.index)

    def _target_side(
        self, pair: str, dates: pd.Series, current_signal: pd.Series
    ) -> pd.Series:
        universe = self._whitelist()
        if pair not in universe:
            universe = [*universe, pair]

        signals = {}
        for candidate in universe:
            signals[candidate] = self._residual_signal_for_pair(candidate, dates)

        frame = pd.DataFrame(signals, index=dates.index)
        target = pd.Series(0, index=dates.index, dtype=int)

        enough = frame.notna().sum(axis=1) >= self.TOP_N + self.BOTTOM_N
        high = frame.rank(axis=1, method="first", ascending=False)
        low = frame.rank(axis=1, method="first", ascending=True)

        target.loc[enough & (high[pair] <= self.TOP_N)] = 1
        target.loc[enough & (low[pair] <= self.BOTTOM_N)] = -1
        return target

    @staticmethod
    def _is_rebalance_bar(dates: pd.Series) -> pd.Series:
        stamps = pd.to_datetime(dates, utc=True)
        return (stamps.dt.weekday == 0) & (stamps.dt.hour == 0)
