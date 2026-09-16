"""P3-EXP-001 research strategies: genuine-futures Turtle, long/short x sizing.

RESEARCH ONLY. This module is deliberately outside `user_data/strategies/` so it
can never be confused with a production strategy. The production
`DonchianTurtleBaseline` is not imported, modified or subclassed.

Frozen signal (identical to the Turtle baseline definition):
* long entry  : ``close > prior 20-bar high`` on the rising edge
* short entry : ``close < prior 20-bar low`` on the rising edge
* long exit   : ``close < prior 10-bar low``
* short exit  : ``close > prior 10-bar high``
* stop        : fixed ``2 x ATR(20)`` from entry, plus a -30% backstop
* ROI disabled, no pyramiding, max 5 open trades, 1x leverage

The experiment requires separating the SIGNAL from the VOLATILITY-SCALED SIZING:

* ``sizing_mode = "raw"`` -> fixed notional per trade (the config stake); the
  signal is traded with no volatility scaling.
* ``sizing_mode = "vol"`` -> 1% of equity risked at the 2xATR stop, i.e. position
  size is inversely proportional to ATR (volatility scaling).

Four concrete classes combine direction and sizing so the ablation is exact.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas import DataFrame

_SHARED_DIR = Path(__file__).resolve().parents[2] / "user_data" / "strategies" / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from freqtrade.persistence import Trade  # noqa: E402
from freqtrade.strategy import IStrategy  # noqa: E402
from pa_indicators import atr, donchian_lower, donchian_upper  # noqa: E402
from pa_risk import (  # noqa: E402
    atr_stop_distance,
    fixed_atr_stop_price,
    risk_based_stake,
    stoploss_ratio_from_fixed_stop,
)
from pa_signals import rising_edge  # noqa: E402


class _TurtleFuturesBase(IStrategy):
    """Shared frozen Turtle mechanics for the P3-EXP-001 arms."""

    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = False
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    use_custom_stoploss = True
    position_adjustment_enable = False

    minimal_roi: dict = {}
    stoploss = -0.30

    # Frozen Turtle parameters (not tunable in P3-EXP-001).
    entry_period: int = 20
    exit_period: int = 10
    atr_period: int = 20
    atr_stop_multiple: float = 2.0
    risk_per_trade: float = 0.01
    max_stake_fraction: float = 1.0

    # Arm switches (overridden by subclasses).
    direction: str = "long"  # "long" | "short"
    sizing_mode: str = "vol"  # "vol" | "raw"

    @property
    def startup_candle_count(self) -> int:
        """
        Warm-up bars for the channels and ATR.

        :return: Number of warm-up candles.
        """
        return max(self.entry_period, self.exit_period, self.atr_period) + 10

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Attach the causal Donchian channels and ATR (frozen Turtle definition).

        :param dataframe: Candle data.
        :param metadata: Freqtrade metadata.
        :return: Enriched frame.
        """
        dataframe["dc_entry_upper"] = donchian_upper(dataframe["high"], self.entry_period)
        dataframe["dc_entry_lower"] = donchian_lower(dataframe["low"], self.entry_period)
        dataframe["dc_exit_lower"] = donchian_lower(dataframe["low"], self.exit_period)
        dataframe["dc_exit_upper"] = donchian_upper(dataframe["high"], self.exit_period)
        dataframe["atr"] = atr(
            dataframe["high"], dataframe["low"], dataframe["close"], self.atr_period
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Emit one entry per breakout episode for the configured direction.

        :param dataframe: Indicator frame.
        :param metadata: Freqtrade metadata.
        :return: Frame with entry columns.
        """
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        if self.direction == "long":
            breakout = (dataframe["close"] > dataframe["dc_entry_upper"]) & dataframe[
                "dc_entry_upper"
            ].notna()
            signals = rising_edge(breakout) & dataframe["atr"].notna()
            dataframe.loc[signals, "enter_long"] = 1
            dataframe.loc[signals, "enter_tag"] = "turtle_breakout_long"
        else:
            breakdown = (dataframe["close"] < dataframe["dc_entry_lower"]) & dataframe[
                "dc_entry_lower"
            ].notna()
            signals = rising_edge(breakdown) & dataframe["atr"].notna()
            dataframe.loc[signals, "enter_short"] = 1
            dataframe.loc[signals, "enter_tag"] = "turtle_breakdown_short"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Emit the channel exit for the configured direction.

        :param dataframe: Indicator frame.
        :param metadata: Freqtrade metadata.
        :return: Frame with exit columns.
        """
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        if self.direction == "long":
            exit_long = (dataframe["close"] < dataframe["dc_exit_lower"]) & dataframe[
                "dc_exit_lower"
            ].notna()
            dataframe.loc[exit_long, "exit_long"] = 1
            dataframe.loc[exit_long, "exit_tag"] = "turtle_channel_exit"
        else:
            exit_short = (dataframe["close"] > dataframe["dc_exit_upper"]) & dataframe[
                "dc_exit_upper"
            ].notna()
            dataframe.loc[exit_short, "exit_short"] = 1
            dataframe.loc[exit_short, "exit_tag"] = "turtle_channel_exit"
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
        Size the position according to the arm's sizing mode.

        ``"raw"`` = fixed notional (the proposed stake, i.e. the config stake).
        ``"vol"`` = 1% risk at the 2xATR stop (volatility scaling).

        :param pair: Pair being entered.
        :param current_time: Current candle time.
        :param current_rate: Proposed entry rate.
        :param proposed_stake: Freqtrade default stake (used by "raw").
        :param min_stake: Exchange minimum.
        :param max_stake: Maximum allowed stake.
        :param leverage: Leverage (1.0).
        :param entry_tag: Entry tag.
        :param side: "long" or "short".
        :return: Stake in quote currency.
        """
        if self.sizing_mode == "raw":
            return min(proposed_stake, max_stake)

        atr_value = self._lookup_atr(pair, current_time)
        if atr_value is None or current_rate <= 0 or atr_value <= 0:
            return proposed_stake
        equity = self._equity_or_default(proposed_stake)
        stop_distance = atr_stop_distance(atr_value, self.atr_stop_multiple)
        if stop_distance <= 0:
            return proposed_stake
        stake = risk_based_stake(
            equity=equity,
            risk_per_trade=self.risk_per_trade,
            stop_distance=stop_distance,
            price=current_rate,
            max_stake_fraction=self.max_stake_fraction,
        )
        stake = min(stake, max_stake)
        if min_stake is not None and stake < min_stake:
            return 0.0
        return stake

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float | None:
        """
        Fixed 2xATR stop measured from entry (both sizing modes).

        :param pair: Pair of the open trade.
        :param trade: The open trade.
        :param current_time: Current time.
        :param current_rate: Current rate.
        :param current_profit: Unused.
        :param after_fill: First call after fill.
        :return: Stop ratio, or None to keep the backstop.
        """
        atr_at_entry = self._atr_for_trade(pair, trade)
        if atr_at_entry is None or atr_at_entry <= 0:
            return None
        side = "short" if getattr(trade, "is_short", False) else "long"
        stop_price = fixed_atr_stop_price(
            entry_price=trade.open_rate,
            atr_at_entry=atr_at_entry,
            atr_multiple=self.atr_stop_multiple,
            side=side,
        )
        return stoploss_ratio_from_fixed_stop(stop_price, current_rate, side=side)

    def _equity_or_default(self, fallback: float) -> float:
        """
        Best-effort equity, falling back to ``fallback``.

        :param fallback: Fallback value.
        :return: Equity estimate.
        """
        try:
            equity = float(self.wallets.get_total_stake_amount())
        except Exception:  # pragma: no cover - runtime dependent
            return fallback
        return equity if equity > 0 else fallback

    def _atr_for_trade(self, pair: str, trade: Trade) -> float | None:
        """
        ATR at entry, cached on the trade.

        :param pair: Pair of the trade.
        :param trade: The open trade.
        :return: ATR or None.
        """
        cached = trade.get_custom_data("atr_entry")
        if cached is not None:
            try:
                value = float(cached)
            except (TypeError, ValueError):
                return None
            return value if value > 0 else None
        atr_value = self._lookup_atr(pair, trade.open_date_utc)
        if atr_value is not None:
            trade.set_custom_data("atr_entry", atr_value)
        return atr_value

    def _lookup_atr(self, pair: str, when: datetime) -> float | None:
        """
        ATR from the last analysed candle at or before ``when``.

        :param pair: Pair to look up.
        :param when: Timestamp bound (inclusive).
        :return: ATR or None.
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        except Exception:  # pragma: no cover - runtime dependent
            return None
        if dataframe is None or dataframe.empty:
            return None
        if "atr" not in dataframe.columns or "date" not in dataframe.columns:
            return None
        subset = dataframe[dataframe["date"] <= when]
        if subset.empty:
            return None
        value = subset["atr"].iloc[-1]
        if pd.isna(value):
            return None
        value = float(value)
        return value if value > 0 else None


class TurtleFuturesLong(_TurtleFuturesBase):
    """Long-only, volatility-scaled sizing (1% risk at the 2xATR stop)."""

    can_short = False
    direction = "long"
    sizing_mode = "vol"


class TurtleFuturesLongRaw(_TurtleFuturesBase):
    """Long-only, raw signal with fixed-notional sizing (no volatility scaling)."""

    can_short = False
    direction = "long"
    sizing_mode = "raw"


class TurtleFuturesShort(_TurtleFuturesBase):
    """Short-only, volatility-scaled sizing."""

    can_short = True
    direction = "short"
    sizing_mode = "vol"


class TurtleFuturesShortRaw(_TurtleFuturesBase):
    """Short-only, raw signal with fixed-notional sizing."""

    can_short = True
    direction = "short"
    sizing_mode = "raw"
