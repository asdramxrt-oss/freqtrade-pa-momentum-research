"""Deterministic synthetic market data helpers for tests.

No test in this project downloads candles or contacts an exchange.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["make_candles"]


def make_candles(closes: list[float], start: str = "2024-01-01") -> pd.DataFrame:
    """
    Build a minimal OHLCV frame from a close series.

    Highs and lows are derived deterministically from the close so that tests
    can reason about exact channel values.

    :param closes: Close prices, in order.
    :param start: Timestamp of the first candle.
    :return: DataFrame with ``date, open, high, low, close, volume``.
    """
    index = pd.date_range(start=start, periods=len(closes), freq="4h", tz="UTC")
    close = pd.Series(closes, index=index, dtype=float)
    open_ = close.shift(1).fillna(close.iloc[0])
    body = pd.concat([open_, close], axis=1)
    high = body.max(axis=1) + 1.0
    low = body.min(axis=1) - 1.0
    return pd.DataFrame(
        {
            "date": index,
            "open": open_.to_numpy(),
            "high": high.to_numpy(),
            "low": low.to_numpy(),
            "close": close.to_numpy(),
            "volume": np.full(len(closes), 100.0),
        }
    )
