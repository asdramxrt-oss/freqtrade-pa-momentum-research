"""Turtle / Donchian absolute-momentum baseline (EXP-001).

This is the reference strategy for the whole research programme. Its only job is
to be a *clean, boring, fully specified* trend follower so that every later
strategy has an honest yardstick to beat.

Deliberate non-goals for this baseline
--------------------------------------
No ML, no regime classifier, no mean reversion, no residual/cross-sectional
momentum, no pair router, no pyramiding, no trailing stop, no optimisation.

Deliberate design choices
-------------------------
* ``entry_period=20`` / ``exit_period=10`` are the *classic* Turtle parameters.
  They are fixed by the specification and are **not** to be tuned to improve a
  backtest. Parameter sensitivity is studied in a separate, pre-registered
  experiment instead.
* Entries use the prior N-bar high (one-bar shifted channel). The current bar's
  high never participates in its own breakout test; see :mod:`pa_indicators`.
* Signals are de-duplicated with :func:`pa_signals.rising_edge` so one breakout
  episode produces exactly one entry signal.
* Risk is ATR-based: a fixed 2N stop and risk-scaled position size. Signal
  generation and risk management live in separate modules
  (:mod:`pa_signals`, :mod:`pa_risk`) so that the signal itself can be tested
  in isolation from sizing.

Hypothesis, validation plan and rejection criteria:
``research/hypotheses/turtle.md``
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
from pa_indicators import atr  # noqa: E402
from pa_risk import (  # noqa: E402
    atr_stop_distance,
    fixed_atr_stop_price,
    risk_based_stake,
    stoploss_ratio_from_fixed_stop,
)
from pa_signals import donchian_breakout_frame  # noqa: E402


class DonchianTurtleBaseline(IStrategy):
    """
    Long-only Donchian breakout trend follower with ATR risk management.

    Breakout entry above the prior ``entry_period``-bar high, channel exit below
    the prior ``exit_period``-bar low, fixed ATR stop, risk-scaled sizing.
    """

    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = False
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Risk is a first-class part of this strategy, so the stop-loss is managed
    # by ``custom_stoploss`` rather than a static percentage.
    use_custom_stoploss = True
    position_adjustment_enable = False

    # ROI is intentionally disabled: in a trend-following system the exit is
    # the channel, not a profit target.
    minimal_roi: dict = {}

    # Static backstop used only if the ATR lookup fails for a trade.
    stoploss = -0.30

    # --- Specification parameters (fixed for EXP-001) ---------------------
    entry_period: int = 20
    exit_period: int = 10
    atr_period: int = 20
    atr_stop_multiple: float = 2.0
    risk_per_trade: float = 0.01
    max_stake_fraction: float = 1.0

    @property
    def startup_candle_count(self) -> int:
        """
        Bars required before indicators are trustworthy.

        Derived from the configured periods so it can never silently lag behind
        a parameter change.

        :return: Number of warm-up candles.
        """
        return max(self.entry_period, self.exit_period, self.atr_period) + 10

    # ------------------------------------------------------------------
    # Indicator layer
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Attach causal Donchian channels and ATR to the candle frame.

        :param dataframe: Candle data with ``date, open, high, low, close, volume``.
        :param metadata: Freqtrade metadata containing the ``pair``.
        :return: The same DataFrame with indicator columns added.
        """
        frame = donchian_breakout_frame(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            entry_period=self.entry_period,
            exit_period=self.exit_period,
        )
        dataframe["dc_entry_upper"] = frame["dc_entry_upper"]
        dataframe["dc_entry_lower"] = frame["dc_entry_lower"]
        dataframe["dc_exit_lower"] = frame["dc_exit_lower"]
        dataframe["atr"] = atr(
            dataframe["high"], dataframe["low"], dataframe["close"], self.atr_period
        )
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        return dataframe

    # ------------------------------------------------------------------
    # Signal layer
    # ------------------------------------------------------------------
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Emit one long entry per causal Donchian breakout episode.

        :param dataframe: Indicator-enriched candle frame.
        :param metadata: Freqtrade metadata containing the ``pair``.
        :return: The same DataFrame with ``enter_long``/``enter_tag`` set.
        """
        dataframe["enter_long"] = 0
        frame = donchian_breakout_frame(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            entry_period=self.entry_period,
            exit_period=self.exit_period,
        )
        signals = frame["first_breakout_up"] & dataframe["atr"].notna()
        dataframe.loc[signals, "enter_long"] = 1
        dataframe.loc[signals, "enter_tag"] = "donchian_breakout"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit long when the close breaks the prior ``exit_period``-bar low.

        :param dataframe: Indicator-enriched candle frame.
        :param metadata: Freqtrade metadata containing the ``pair``.
        :return: The same DataFrame with ``exit_long``/``exit_tag`` set.
        """
        dataframe["exit_long"] = 0
        frame = donchian_breakout_frame(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            entry_period=self.entry_period,
            exit_period=self.exit_period,
        )
        signals = frame["exit_long"]
        dataframe.loc[signals, "exit_long"] = 1
        dataframe.loc[signals, "exit_tag"] = "donchian_exit"
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

        Falls back to ``proposed_stake`` whenever ATR or equity is unavailable,
        so the baseline never silently stops trading because of a sizing lookup
        failure.

        :param pair: Pair being entered.
        :param current_time: Current candle time.
        :param current_rate: Proposed entry rate.
        :param proposed_stake: Freqtrade's default stake.
        :param min_stake: Exchange minimum stake, if known.
        :param max_stake: Maximum allowed stake.
        :param leverage: Leverage for the trade (always 1.0 in spot research).
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

        The ATR used is the one observed at (or before) entry, retrieved from
        the analyzed dataframe and cached on the trade. Nothing about the future
        enters this calculation.

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
        stop_price = fixed_atr_stop_price(
            entry_price=trade.open_rate,
            atr_at_entry=atr_at_entry,
            atr_multiple=self.atr_stop_multiple,
            side="long",
        )
        return stoploss_ratio_from_fixed_stop(stop_price, current_rate)

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
