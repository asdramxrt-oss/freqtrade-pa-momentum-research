"""Risk and position-sizing helpers for price-action momentum strategies.

These helpers are intentionally free of any signal logic and free of any
``freqtrade`` import. They take explicit numbers and return explicit numbers so
that position sizing can be tested without a running bot.
"""

from __future__ import annotations

__all__ = [
    "atr_stop_distance",
    "fixed_atr_stop_price",
    "stoploss_ratio_from_fixed_stop",
    "risk_based_stake",
]


def atr_stop_distance(atr_value: float, atr_multiple: float) -> float:
    """
    Absolute stop distance implied by ``atr_multiple`` ATRs.

    :param atr_value: ATR in price units. Must be positive.
    :param atr_multiple: Stop distance in ATRs. Must be positive.
    :return: Stop distance in price units.
    :raises ValueError: If either argument is not strictly positive.
    """
    if atr_value <= 0:
        raise ValueError(f"atr_value must be > 0, got {atr_value!r}")
    if atr_multiple <= 0:
        raise ValueError(f"atr_multiple must be > 0, got {atr_multiple!r}")
    return atr_value * atr_multiple


def fixed_atr_stop_price(
    entry_price: float,
    atr_at_entry: float,
    atr_multiple: float = 2.0,
    side: str = "long",
) -> float:
    """
    Stop price for a fixed (non-trailing) ATR stop measured from entry.

    :param entry_price: Trade entry price. Must be positive.
    :param atr_at_entry: ATR captured at entry, in price units.
    :param atr_multiple: Stop distance in ATRs.
    :param side: ``"long"`` or ``"short"``.
    :return: Stop price.
    :raises ValueError: On non-positive price or an unknown side.
    """
    if entry_price <= 0:
        raise ValueError(f"entry_price must be > 0, got {entry_price!r}")
    distance = atr_stop_distance(atr_at_entry, atr_multiple)
    if side == "long":
        return entry_price - distance
    if side == "short":
        return entry_price + distance
    raise ValueError(f"side must be 'long' or 'short', got {side!r}")


def stoploss_ratio_from_fixed_stop(
    stop_price: float,
    current_rate: float,
    side: str = "long",
) -> float:
    """
    Convert an absolute stop price into the ratio ``freqtrade`` expects.

    ``freqtrade``'s ``custom_stoploss`` returns the stop distance relative to the
    *current* rate. The engine always applies ``abs()`` and then places the stop
    **below** the current rate for a long and **above** it for a short, so the
    magnitude is what matters. The signs below therefore follow the documented
    convention (long negative, short positive) rather than the engine's internal
    handling:

    * long: a stop below the current rate returns a negative ratio.
    * short: a stop above the current rate returns a positive ratio.

    If the stop has already been passed (stop above current for a long, or below
    current for a short), the ratio is clamped to a tiny value on the correct
    side of zero. Clamping is deliberate: a fractionally-through stop triggers an
    immediate exit, which is the intended behaviour when the stop is already hit.

    :param stop_price: Absolute stop price.
    :param current_rate: Current market rate. Must be positive.
    :param side: ``"long"`` or ``"short"``.
    :return: Ratio in ``[-1, 0)`` for longs and ``(0, 1]`` for shorts.
    :raises ValueError: If ``current_rate`` is not strictly positive, or ``side``
        is not ``"long"`` or ``"short"``.
    """
    if current_rate <= 0:
        raise ValueError(f"current_rate must be > 0, got {current_rate!r}")
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side!r}")
    ratio = (stop_price - current_rate) / current_rate
    if side == "long":
        if ratio >= 0:
            return -1e-9
        return max(ratio, -1.0)
    if ratio <= 0:
        return 1e-9
    return min(ratio, 1.0)


def risk_based_stake(
    equity: float,
    risk_per_trade: float,
    stop_distance: float,
    price: float,
    max_stake_fraction: float = 1.0,
) -> float:
    """
    Position size that risks a fixed fraction of equity on the stop distance.

    ``stake = equity * risk_per_trade * price / stop_distance``

    A wider stop therefore produces a smaller position. The result is capped by
    ``max_stake_fraction * equity`` so a very tight stop cannot demand more
    capital than the account has.

    :param equity: Account equity in quote currency.
    :param risk_per_trade: Fraction of equity risked per trade, e.g. ``0.01``.
    :param stop_distance: Absolute stop distance in price units.
    :param price: Entry price.
    :param max_stake_fraction: Hard cap on the stake as a fraction of equity.
    :return: Stake in quote currency, always >= 0.
    :raises ValueError: On non-positive inputs.
    """
    if equity <= 0:
        raise ValueError(f"equity must be > 0, got {equity!r}")
    if price <= 0:
        raise ValueError(f"price must be > 0, got {price!r}")
    if stop_distance <= 0:
        raise ValueError(f"stop_distance must be > 0, got {stop_distance!r}")
    if not 0 < risk_per_trade <= 1:
        raise ValueError(f"risk_per_trade must be in (0, 1], got {risk_per_trade!r}")
    if not 0 < max_stake_fraction <= 1:
        raise ValueError(f"max_stake_fraction must be in (0, 1], got {max_stake_fraction!r}")

    risk_amount = equity * risk_per_trade
    units = risk_amount / stop_distance
    stake = units * price
    return max(0.0, min(stake, equity * max_stake_fraction))
