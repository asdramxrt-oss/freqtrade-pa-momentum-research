"""Unit tests for causal price-structure primitives."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pa_structure import (
    bars_since_event,
    confirmed_swing_high,
    confirmed_swing_low,
    max_since_event,
    min_since_event,
    value_at_last_event,
)


def _series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


def _assert_same_finite(left: pd.Series, right: pd.Series) -> None:
    """
    Assert two series agree, including on where they are NaN.

    :param left: First series.
    :param right: Second series.
    """
    left_values = np.asarray(left, dtype=float)
    right_values = np.asarray(right, dtype=float)
    assert left_values.shape == right_values.shape
    assert (np.isnan(left_values) == np.isnan(right_values)).all()
    finite = ~np.isnan(left_values)
    assert left_values[finite].tolist() == pytest.approx(right_values[finite].tolist())


class TestConfirmedSwings:
    """Swing points must be published only after their confirmation delay."""

    def test_swing_high_is_published_after_right_bars(self) -> None:
        high = _series([1.0, 2.0, 3.0, 2.0, 1.0, 5.0, 1.0, 1.0])

        published = confirmed_swing_high(high, left=2, right=2)

        assert np.isnan(published.iloc[2])
        assert published.iloc[4] == pytest.approx(3.0)
        assert published.iloc[7] == pytest.approx(5.0)
        assert published.iloc[[0, 1, 3, 5, 6]].isna().all()

    def test_swing_low_is_published_after_right_bars(self) -> None:
        low = _series([5.0, 4.0, 1.0, 4.0, 5.0, 0.5, 5.0, 5.0])

        published = confirmed_swing_low(low, left=2, right=2)

        assert np.isnan(published.iloc[2])
        assert published.iloc[4] == pytest.approx(1.0)
        assert published.iloc[7] == pytest.approx(0.5)

    def test_no_value_before_the_confirmation_bar(self) -> None:
        high = _series([1.0, 2.0, 100.0, 2.0, 1.0])

        published = confirmed_swing_high(high, left=1, right=1)

        assert published.iloc[:3].isna().all()
        assert published.iloc[3] == pytest.approx(100.0)

    def test_swing_detection_is_prefix_invariant(self) -> None:
        rng = np.random.default_rng(7)
        high = _series(list(rng.uniform(100, 120, size=80)))

        full = confirmed_swing_high(high, left=2, right=2)
        truncated = confirmed_swing_high(high.iloc[:50], left=2, right=2)

        _assert_same_finite(full.iloc[:50], truncated)

    def test_rejects_non_positive_windows(self) -> None:
        high = _series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError):
            confirmed_swing_high(high, left=0, right=2)
        with pytest.raises(ValueError):
            confirmed_swing_low(high, left=2, right=0)


class TestEventHelpers:
    """Elapsed-bar counters and since-event extremes."""

    def test_bars_since_event_counts_from_zero(self) -> None:
        condition = pd.Series([False, True, False, False, True, False], dtype=bool)

        elapsed = bars_since_event(condition)

        assert np.isnan(elapsed.iloc[0])
        assert elapsed.iloc[1] == pytest.approx(0.0)
        assert elapsed.iloc[2] == pytest.approx(1.0)
        assert elapsed.iloc[3] == pytest.approx(2.0)
        assert elapsed.iloc[4] == pytest.approx(0.0)
        assert elapsed.iloc[5] == pytest.approx(1.0)

    def test_min_since_event_resets_at_each_event(self) -> None:
        values = _series([10.0, 8.0, 9.0, 5.0, 7.0, 6.0])
        condition = pd.Series([True, False, False, True, False, False], dtype=bool)

        result = min_since_event(values, condition)

        assert result.tolist() == pytest.approx([10.0, 8.0, 8.0, 5.0, 5.0, 5.0])

    def test_max_since_event_resets_at_each_event(self) -> None:
        values = _series([10.0, 12.0, 9.0, 5.0, 7.0, 6.0])
        condition = pd.Series([True, False, False, True, False, False], dtype=bool)

        result = max_since_event(values, condition)

        assert result.tolist() == pytest.approx([10.0, 12.0, 12.0, 5.0, 7.0, 7.0])

    def test_value_at_last_event_carries_forward(self) -> None:
        values = _series([10.0, 10.0, 20.0, 20.0, 20.0, 30.0, 30.0, 30.0])
        condition = pd.Series([False, False, True, False, False, True, False, False])

        result = value_at_last_event(values, condition)

        assert np.isnan(result.iloc[0])
        assert result.iloc[2:5].tolist() == pytest.approx([20.0, 20.0, 20.0])
        assert result.iloc[5:].tolist() == pytest.approx([30.0, 30.0, 30.0])

    def test_nan_condition_is_treated_as_false(self) -> None:
        condition = pd.Series([np.nan, True, np.nan], dtype=object)

        elapsed = bars_since_event(condition)

        assert np.isnan(elapsed.iloc[0])
        assert elapsed.iloc[1] == pytest.approx(0.0)
        assert elapsed.iloc[2] == pytest.approx(1.0)
