"""Pullback-continuation baseline for EXP-003 (standalone, rule-based, no ML).

Entry geometry (frozen in ``research/experiment_specs/EXP-003.md`` §4)::

    direction (impulse)  ->  controlled pullback  ->  structure holds
                         ->  continuation confirmation  ->  entry at next open

Long and short are exact mirrors. The setup lives in :mod:`pa_pullback` and the
causal structure primitives in :mod:`pa_structure`; this file only wires them to
freqtrade and applies the same ATR stop / channel exit / risk-based sizing as the
reference breakout baseline, so that a comparison isolates the *entry*.

Direction scope is a class attribute, and three thin subclasses expose the three
pre-registered variants:

* :class:`PullbackContinuation`      -- long + short (primary object)
* :class:`PullbackContinuationLong`  -- long only (also the spot control)
* :class:`PullbackContinuationShort` -- short only

This strategy never references the breakout baseline's signals.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas import DataFrame

# The shared package lives outside the strategy folder so that it can be reused
# by every strategy family and imported by tests without loading freqtrade.
_SHARED_DIR = Path(__file__).resolve().parent.parent / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from freqtrade.persistence import Trade  # noqa: E402
from freqtrade.strategy import IStrategy  # noqa: E402
from pa_pullback import pullback_continuation_frame  # noqa: E402
from pa_risk import (  # noqa: E402
    atr_stop_distance,
    fixed_atr_stop_price,
    risk_based_stake,
    stoploss_ratio_from_fixed_stop,
)


class PullbackContinuationBase(IStrategy):
    """
    Price-action pullback continuation with ATR risk management.

    Direction is controlled by :attr:`direction_scope`; the base class is the
    combined variant. Concrete subclasses fix the scope and ``can_short`` flag.
    """

    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = True
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    use_custom_stoploss = True
    position_adjustment_enable = False

    # ROI is intentionally disabled: the exit is the channel, not a profit target.
    minimal_roi: dict = {}
    stoploss = -0.30

    # ``"both"`` | ``"long"`` | ``"short"`` -- fixed per subclass.
    direction_scope = "both"

    # --- Specification parameters (frozen for EXP-003) --------------------
    swing_left: int = 2
    swing_right: int = 2
    atr_period: int = 20
    impulse_min_atr: float = 3.0
    pullback_min_atr: float = 0.5
    pullback_max_atr: float = 2.0
    max_pullback_bars: int = 10
    confirm_bars: int = 3
    exit_period: int = 10
    atr_stop_multiple: float = 2.0
    risk_per_trade: float = 0.01
    max_stake_fraction: float = 1.0

    @property
    def startup_candle_count(self) -> int:
        """
        Bars required before the setup and its ATR are trustworthy.

        :return: Number of warm-up candles.
        """
        return (
            max(
                self.swing_left + self.swing_right + 1,
                self.atr_period,
                self.exit_period,
                self.max_pullback_bars,
                self.confirm_bars,
            )
            + 10
        )

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _setup_frame(self, dataframe: DataFrame) -> DataFrame:
        """
        Compute the pullback-continuation frame for one pair.

        :param dataframe: Candle frame with ``open, high, low, close``.
        :return: Setup frame from :func:`pa_pullback.pullback_continuation_frame`.
        """
        return pullback_continuation_frame(
            dataframe["open"],
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            swing_left=self.swing_left,
            swing_right=self.swing_right,
            atr_period=self.atr_period,
            impulse_min_atr=self.impulse_min_atr,
            pullback_min_atr=self.pullback_min_atr,
            pullback_max_atr=self.pullback_max_atr,
            max_pullback_bars=self.max_pullback_bars,
            confirm_bars=self.confirm_bars,
            exit_period=self.exit_period,
        )

    # ------------------------------------------------------------------
    # freqtrade layers
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Attach the setup, its diagnostics and its geometry to the candle frame.

        :param dataframe: Candle data.
        :param metadata: Freqtrade metadata containing the ``pair``.
        :return: The same DataFrame with setup columns added.
        """
        setup = self._setup_frame(dataframe)
        for column in setup.columns:
            dataframe[column] = setup[column]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Emit pullback-continuation entries allowed by ``direction_scope``.

        :param dataframe: Indicator-enriched candle frame.
        :param metadata: Freqtrade metadata containing the ``pair``.
        :return: The same DataFrame with entry columns set.
        """
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        setup = self._setup_frame(dataframe)
        if self.direction_scope in ("long", "both"):
            long_signals = setup["long_signal"] & dataframe["atr"].notna()
            dataframe.loc[long_signals, "enter_long"] = 1
            dataframe.loc[long_signals, "enter_tag"] = "pullback_continuation_long"
        if self.direction_scope in ("short", "both"):
            short_signals = setup["short_signal"] & dataframe["atr"].notna()
            dataframe.loc[short_signals, "enter_short"] = 1
            dataframe.loc[short_signals, "enter_tag"] = "pullback_continuation_short"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Emit causal channel exits for both directions.

        :param dataframe: Indicator-enriched candle frame.
        :param metadata: Freqtrade metadata containing the ``pair``.
        :return: The same DataFrame with exit columns set.
        """
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        setup = self._setup_frame(dataframe)
        dataframe.loc[setup["exit_long_signal"], "exit_long"] = 1
        dataframe.loc[setup["exit_long_signal"], "exit_tag"] = "donchian_exit"
        dataframe.loc[setup["exit_short_signal"], "exit_short"] = 1
        dataframe.loc[setup["exit_short_signal"], "exit_tag"] = "donchian_exit"
        return dataframe

    # ------------------------------------------------------------------
    # Risk layer
    # ------------------------------------------------------------------
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
        Size the position so that the ATR stop risks ``risk_per_trade`` of equity.

        :param pair: Pair being entered.
        :param current_time: Current candle time.
        :param current_rate: Proposed entry rate.
        :param proposed_stake: Freqtrade's default stake.
        :param min_stake: Exchange minimum stake, if known.
        :param max_stake: Maximum allowed stake.
        :param leverage: Leverage for the trade (1.0 in this research).
        :param entry_tag: Tag of the triggering signal.
        :param side: ``"long"`` or ``"short"``.
        :return: Stake amount in quote currency.
        """
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
        Return the ratio for a fixed 2N stop measured from the entry price.

        :param pair: Pair of the open trade.
        :param trade: The open trade.
        :param current_time: Current candle time.
        :param current_rate: Current rate.
        :param current_profit: Current profit ratio (unused).
        :param after_fill: True on the first call after the entry order filled.
        :return: Stop ratio in ``[-1, 0)``, or ``None`` to keep the backstop.
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _equity_or_default(self, fallback: float) -> float:
        """
        Best-effort total stake amount, falling back to ``fallback``.

        :param fallback: Value to use when the wallet is unavailable.
        :return: Account equity estimate in quote currency.
        """
        try:
            equity = float(self.wallets.get_total_stake_amount())
        except Exception:  # pragma: no cover - depends on runtime mode
            return fallback
        return equity if equity > 0 else fallback

    def _atr_for_trade(self, pair: str, trade: Trade) -> float | None:
        """
        ATR at trade entry, cached on the trade after the first lookup.

        :param pair: Pair of the trade.
        :param trade: The open trade.
        :return: ATR in price units, or ``None`` when unavailable.
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
        ATR from the last analyzed candle at or before ``when``.

        Causal by construction: only candles up to ``when`` are considered.

        :param pair: Pair to look up.
        :param when: Timestamp the value must not exceed.
        :return: ATR in price units, or ``None`` when unavailable.
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        except Exception:  # pragma: no cover - depends on runtime mode
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


class PullbackContinuation(PullbackContinuationBase):
    """Combined long+short pullback continuation (primary EXP-003 object)."""

    can_short = True
    direction_scope = "both"


class PullbackContinuationLong(PullbackContinuationBase):
    """Long-only pullback continuation (also the spot control)."""

    can_short = False
    direction_scope = "long"


class PullbackContinuationShort(PullbackContinuationBase):
    """Short-only pullback continuation."""

    can_short = True
    direction_scope = "short"
