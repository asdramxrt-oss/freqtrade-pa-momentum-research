"""Unit tests for the causal indicator library."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pa_indicators import (
    atr,
    donchian_lower,
    donchian_mid,
    donchian_upper,
    donchian_width,
    rolling_high,
    rolling_low,
    true_range,
    wilder_smooth,
)


def _series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


def _assert_same_finite(left: pd.Series, right: pd.Series) -> None:
    """
    Assert two series agree, including on where they are NaN.

    ``pytest.approx`` cannot compare NaN, so the finite values are compared
    explicitly and the NaN masks are compared separately.

    :param left: First series.
    :param right: Second series.
    """
    left_values = np.asarray(left, dtype=float)
    right_values = np.asarray(right, dtype=float)
    assert left_values.shape == right_values.shape
    assert (np.isnan(left_values) == np.isnan(right_values)).all()
    finite = ~np.isnan(left_values)
    assert left_values[finite].tolist() == pytest.approx(right_values[finite].tolist())


class TestTrueRange:
    """Wilder true range."""

    def test_matches_hand_calculation(self) -> None:
        high = _series([10.0, 12.0, 11.0])
        low = _series([9.0, 10.0, 9.0])
        close = _series([9.5, 11.0, 9.5])

        result = true_range(high, low, close)

        assert result.tolist() == pytest.approx([1.0, 2.5, 2.0])

    def test_first_bar_is_high_minus_low(self) -> None:
        high = _series([10.0, 10.0])
        low = _series([7.0, 9.0])
        close = _series([8.0, 9.5])

        assert true_range(high, low, close).iloc[0] == pytest.approx(3.0)

    def test_is_never_negative(self) -> None:
        high = _series([10.0, 11.0, 12.0, 13.0])
        low = _series([9.0, 10.0, 11.0, 12.0])
        close = _series([9.5, 10.5, 11.5, 12.5])

        assert (true_range(high, low, close) >= 0).all()


class TestWilderSmooth:
    """Wilder smoothing seed and recursion."""

    def test_sma_seed_then_recursion(self) -> None:
        result = wilder_smooth(_series([1.0, 2.0, 3.0, 4.0, 5.0]), period=3)

        assert np.isnan(result.iloc[0])
        assert np.isnan(result.iloc[1])
        assert result.iloc[2] == pytest.approx(2.0)
        assert result.iloc[3] == pytest.approx((2.0 * 2 + 4.0) / 3)
        assert result.iloc[4] == pytest.approx((2.0 * ((2.0 * 2 + 4.0) / 3) + 5.0) / 3)

    def test_returns_all_nan_when_series_shorter_than_period(self) -> None:
        result = wilder_smooth(_series([1.0, 2.0]), period=5)

        assert result.isna().all()

    def test_rejects_non_positive_period(self) -> None:
        with pytest.raises(ValueError):
            wilder_smooth(_series([1.0, 2.0]), period=0)


class TestAtr:
    """Average true range."""

    def test_first_period_minus_one_values_are_nan(self) -> None:
        high = _series([float(i) + 2 for i in range(30)])
        low = _series([float(i) for i in range(30)])
        close = _series([float(i) + 1 for i in range(30)])

        result = atr(high, low, close, period=14)

        assert result.iloc[:13].isna().all()
        assert not np.isnan(result.iloc[13])
        assert result.iloc[13:].notna().all()

    def test_matches_manual_wilder_recursion(self) -> None:
        high = _series([10.0, 11.0, 13.0, 12.0, 14.0, 15.0, 14.5, 16.0])
        low = _series([9.0, 9.5, 11.0, 10.5, 12.0, 13.0, 12.5, 14.0])
        close = _series([9.5, 10.5, 12.0, 11.0, 13.5, 14.0, 13.0, 15.5])
        period = 4

        tr = true_range(high, low, close)
        expected = float(np.mean(tr.iloc[:period]))
        manual = [expected]
        for index in range(period, len(tr)):
            expected = ((period - 1) * expected + float(tr.iloc[index])) / period
            manual.append(expected)

        result = atr(high, low, close, period=period)

        assert result.iloc[period - 1 :].tolist() == pytest.approx(manual)

    def test_atr_is_prefix_invariant(self) -> None:
        high = _series([10.0, 11.0, 13.0, 12.0, 14.0, 15.0])
        low = _series([9.0, 9.5, 11.0, 10.5, 12.0, 13.0])
        close = _series([9.5, 10.5, 12.0, 11.0, 13.5, 14.0])

        full = atr(high, low, close, period=3)
        truncated = atr(high.iloc[:4], low.iloc[:4], close.iloc[:4], period=3)

        _assert_same_finite(full.iloc[:4], truncated)


class TestDonchian:
    """Donchian channels must use only prior bars."""

    def test_upper_channel_excludes_current_bar(self) -> None:
        high = _series([float(i) for i in range(1, 26)])

        result = donchian_upper(high, period=20)

        assert np.isnan(result.iloc[19])
        assert result.iloc[20] == pytest.approx(20.0)
        assert result.iloc[24] == pytest.approx(24.0)
        assert result.iloc[24] < high.iloc[24]

    def test_lower_channel_excludes_current_bar(self) -> None:
        low = _series([float(i) for i in range(1, 26)])

        result = donchian_lower(low, period=10)

        assert np.isnan(result.iloc[9])
        assert result.iloc[10] == pytest.approx(1.0)
        assert result.iloc[24] == pytest.approx(15.0)

    def test_a_new_extreme_never_lifts_its_own_channel(self) -> None:
        high = _series([5.0] * 10 + [1000.0])

        result = donchian_upper(high, period=5)

        assert result.iloc[10] == pytest.approx(5.0)

    def test_is_prefix_invariant(self) -> None:
        rng = np.random.default_rng(1234)
        high = _series(list(rng.uniform(100, 120, size=60)))

        full = donchian_upper(high, period=15)
        truncated = donchian_upper(high.iloc[:30], period=15)

        _assert_same_finite(full.iloc[:30], truncated)

    def test_mid_is_average_of_channels(self) -> None:
        high = _series([float(i) + 1 for i in range(30)])
        low = _series([float(i) - 1 for i in range(30)])

        result = donchian_mid(high, low, period=5)

        expected = (donchian_upper(high, 5) + donchian_lower(low, 5)) / 2.0
        assert result.iloc[10:].tolist() == pytest.approx(expected.iloc[10:].tolist())

    def test_width_normalisation_is_scale_free(self) -> None:
        high = _series([float(i) + 1 for i in range(30)])
        low = _series([float(i) - 1 for i in range(30)])

        raw = donchian_width(high, low, period=5, normalise=False)
        scaled = donchian_width(high * 10, low * 10, period=5, normalise=True)
        normal = donchian_width(high, low, period=5, normalise=True)
        mid = donchian_mid(high, low, period=5)

        assert normal.iloc[10:].tolist() == pytest.approx(scaled.iloc[10:].tolist())
        assert raw.iloc[10] == pytest.approx(normal.iloc[10] * float(mid.iloc[10]))

    def test_rejects_non_positive_period(self) -> None:
        high = _series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError):
            donchian_upper(high, period=0)
        with pytest.raises(ValueError):
            rolling_low(high, period=-1)


class TestRollingHelpers:
    """Generic rolling extremes."""

    def test_shift_zero_includes_current_bar(self) -> None:
        series = _series([1.0, 5.0, 2.0])

        assert rolling_high(series, period=2, shift=0).iloc[1] == pytest.approx(5.0)

    def test_shift_one_excludes_current_bar(self) -> None:
        series = _series([1.0, 5.0, 2.0])

        result = rolling_high(series, period=2, shift=1)

        # At bar 1 the shifted window would cover [-1, 0], so the value is not
        # yet available. At bar 2 it covers [0, 1] and must exclude bar 2.
        assert np.isnan(result.iloc[1])
        assert result.iloc[2] == pytest.approx(5.0)
