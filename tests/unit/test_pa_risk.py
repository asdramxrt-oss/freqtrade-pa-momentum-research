"""Unit tests for risk management and position sizing."""

from __future__ import annotations

import pytest
from pa_risk import (
    atr_stop_distance,
    fixed_atr_stop_price,
    risk_based_stake,
    stoploss_ratio_from_fixed_stop,
)


class TestAtrStopDistance:
    """Stop distance arithmetic."""

    def test_multiplies_atr_by_multiple(self) -> None:
        assert atr_stop_distance(2.0, 3.0) == pytest.approx(6.0)

    def test_rejects_non_positive_atr(self) -> None:
        with pytest.raises(ValueError):
            atr_stop_distance(0.0, 2.0)

    def test_rejects_non_positive_multiple(self) -> None:
        with pytest.raises(ValueError):
            atr_stop_distance(1.0, 0.0)


class TestFixedAtrStopPrice:
    """Fixed ATR stop placement."""

    def test_long_stop_is_below_entry(self) -> None:
        assert fixed_atr_stop_price(100.0, 2.0, 2.0, "long") == pytest.approx(96.0)

    def test_short_stop_is_above_entry(self) -> None:
        assert fixed_atr_stop_price(100.0, 2.0, 2.0, "short") == pytest.approx(104.0)

    def test_rejects_non_positive_entry(self) -> None:
        with pytest.raises(ValueError):
            fixed_atr_stop_price(0.0, 2.0)

    def test_rejects_unknown_side(self) -> None:
        with pytest.raises(ValueError):
            fixed_atr_stop_price(100.0, 2.0, side="sideways")


class TestStoplossRatio:
    """Conversion to freqtrade's relative stop format."""

    def test_ratio_is_negative_below_current_rate(self) -> None:
        assert stoploss_ratio_from_fixed_stop(95.0, 100.0) == pytest.approx(-0.05)

    def test_ratio_is_clamped_when_stop_already_passed(self) -> None:
        result = stoploss_ratio_from_fixed_stop(105.0, 100.0)

        assert result < 0
        assert result > -1e-6

    def test_ratio_is_never_below_minus_one(self) -> None:
        assert stoploss_ratio_from_fixed_stop(1.0, 100.0) >= -1.0

    def test_rejects_non_positive_current_rate(self) -> None:
        with pytest.raises(ValueError):
            stoploss_ratio_from_fixed_stop(95.0, 0.0)

    def test_short_ratio_is_positive_above_current_rate(self) -> None:
        assert stoploss_ratio_from_fixed_stop(105.0, 100.0, side="short") == pytest.approx(0.05)

    def test_short_ratio_clamped_when_stop_already_passed(self) -> None:
        result = stoploss_ratio_from_fixed_stop(95.0, 100.0, side="short")

        assert result > 0
        assert result < 1e-6

    def test_short_ratio_is_never_above_one(self) -> None:
        assert stoploss_ratio_from_fixed_stop(1_000.0, 100.0, side="short") <= 1.0

    def test_long_and_short_are_mirror_images(self) -> None:
        long_ratio = stoploss_ratio_from_fixed_stop(96.0, 100.0, side="long")
        short_ratio = stoploss_ratio_from_fixed_stop(104.0, 100.0, side="short")

        assert long_ratio == pytest.approx(-short_ratio)

    def test_rejects_unknown_side(self) -> None:
        with pytest.raises(ValueError):
            stoploss_ratio_from_fixed_stop(95.0, 100.0, side="sideways")


class TestRiskBasedStake:
    """Risk-scaled position sizing."""

    def test_stake_risks_requested_fraction_of_equity(self) -> None:
        stake = risk_based_stake(
            equity=10_000.0, risk_per_trade=0.01, stop_distance=5.0, price=100.0
        )

        # 1% of 10k = 100 risked over a 5.0 stop distance = 20 units = 2000 quote.
        assert stake == pytest.approx(2_000.0)

    def test_wider_stop_produces_smaller_position(self) -> None:
        tight = risk_based_stake(10_000.0, 0.01, 2.0, 100.0)
        wide = risk_based_stake(10_000.0, 0.01, 8.0, 100.0)

        assert wide < tight

    def test_stake_never_exceeds_equity_cap(self) -> None:
        stake = risk_based_stake(
            equity=1_000.0, risk_per_trade=1.0, stop_distance=0.01, price=100.0
        )

        assert stake == pytest.approx(1_000.0)

    def test_max_stake_fraction_caps_result(self) -> None:
        stake = risk_based_stake(
            equity=10_000.0,
            risk_per_trade=0.5,
            stop_distance=1.0,
            price=100.0,
            max_stake_fraction=0.25,
        )

        assert stake == pytest.approx(2_500.0)

    @pytest.mark.parametrize(
        ("equity", "risk", "stop_distance", "price"),
        [
            (0.0, 0.01, 5.0, 100.0),
            (10_000.0, 0.0, 5.0, 100.0),
            (10_000.0, 0.01, 0.0, 100.0),
            (10_000.0, 0.01, 5.0, 0.0),
            (10_000.0, 1.5, 5.0, 100.0),
        ],
    )
    def test_rejects_invalid_inputs(
        self, equity: float, risk: float, stop_distance: float, price: float
    ) -> None:
        with pytest.raises(ValueError):
            risk_based_stake(equity, risk, stop_distance, price)

    def test_rejects_invalid_max_stake_fraction(self) -> None:
        with pytest.raises(ValueError):
            risk_based_stake(10_000.0, 0.01, 5.0, 100.0, max_stake_fraction=1.5)
