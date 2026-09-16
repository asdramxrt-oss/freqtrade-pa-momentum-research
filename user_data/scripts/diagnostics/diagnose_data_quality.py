"""PHASE 2 diagnostic: data quality of the research candle set.

Checks gaps, duplicates, timestamp monotonicity, timezone handling, the
spot-vs-futures mirror assumption, final-candle completeness and per-pair
listing starts. Read-only: no historical result is altered.

Usage::

    python user_data/scripts/diagnostics/diagnose_data_quality.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diag_common import PAIRS, PERIODS, PROJECT_ROOT, load_candles, write_json  # noqa: E402

OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_data_quality.json"
STEP = pd.Timedelta(hours=4)


def _pair_quality(symbol: str) -> dict:
    """
    Quality report for one pair over the whole file and each period.

    :param symbol: Base symbol.
    :return: Quality summary.
    """
    frame = load_candles(symbol)
    dates = pd.to_datetime(frame["date"], utc=True)
    gaps = dates.diff().dropna()
    report = {
        "rows": int(len(frame)),
        "first": str(dates.iloc[0]),
        "last": str(dates.iloc[-1]),
        "duplicate_timestamps": int(dates.duplicated().sum()),
        "is_monotonic_increasing": bool(dates.is_monotonic_increasing),
        "tz_aware": bool(getattr(dates.dt, "tz", None) is not None),
        "gaps_gt_one_bar": int((gaps > STEP).sum()),
        "max_gap_hours": float(gaps.max() / pd.Timedelta(hours=1)) if len(gaps) else 0.0,
        "periods": {},
    }
    for period, (start, end) in PERIODS.items():
        cut = frame.loc[
            (dates >= pd.Timestamp(start, tz="UTC")) & (dates < pd.Timestamp(end, tz="UTC"))
        ]
        if cut.empty:
            report["periods"][period] = {"rows": 0}
            continue
        cut_dates = pd.to_datetime(cut["date"], utc=True)
        span = cut_dates.iloc[-1] - cut_dates.iloc[0]
        expected = int(span / STEP) + 1
        report["periods"][period] = {
            "rows": int(len(cut)),
            "expected_rows": expected,
            "missing_rows": expected - int(len(cut)),
            "first": str(cut_dates.iloc[0]),
            "last": str(cut_dates.iloc[-1]),
            "duplicates": int(cut_dates.duplicated().sum()),
        }
    return report


def _mirror_check(symbol: str) -> dict:
    """
    Verify the futures mirror equals the spot candles for a pair.

    :param symbol: Base symbol.
    :return: Comparison summary.
    """
    spot = load_candles(symbol, futures=False)
    try:
        futures = load_candles(symbol, futures=True)
    except FileNotFoundError:
        return {"symbol": symbol, "mirror_present": False}
    columns = ["open", "high", "low", "close", "volume"]
    aligned = spot[["date", *columns]].merge(futures[["date", *columns]], on="date", how="inner")
    max_abs = {
        column: float(np.max(np.abs(aligned[f"{column}_x"] - aligned[f"{column}_y"])))
        for column in columns
    }
    return {
        "symbol": symbol,
        "mirror_present": True,
        "overlapping_rows": int(len(aligned)),
        "max_abs_diff": max_abs,
        "identical": all(value == 0.0 for value in max_abs.values()),
    }


def main() -> int:
    """
    Run the data-quality audit and write the result.

    :return: Process exit code.
    """
    report = {
        "phase": "PHASE2",
        "generated_utc": datetime.now(UTC).isoformat(),
        "step_hours": 4,
        "pairs": {symbol: _pair_quality(symbol) for symbol in PAIRS},
        "mirror_checks": [_mirror_check(symbol) for symbol in PAIRS],
        "now_utc": datetime.now(UTC).isoformat(),
    }

    # Final-candle completeness: a 4h candle opening at T is complete once T+4h
    # has passed. Flag any file whose last candle opened less than 4h before now.
    for data in report["pairs"].values():
        last = pd.Timestamp(data["last"])
        data["last_candle_complete"] = (datetime.now(UTC) - last.to_pydatetime()) >= pd.Timedelta(
            hours=4
        )

    write_json(OUTPUT, report)

    print("PAIR    rows   first                last                 gap>1  dup  mirror")
    for symbol in PAIRS:
        data = report["pairs"][symbol]
        mirror = next(m for m in report["mirror_checks"] if m["symbol"] == symbol)
        print(
            f"{symbol:6} {data['rows']:6} {data['first'][:19]}  {data['last'][:19]}  "
            f"{data['gaps_gt_one_bar']:5} {data['duplicate_timestamps']:4}  "
            f"{'identical' if mirror.get('identical') else 'DIFFERS'}"
        )
    missing_total = sum(
        p["missing_rows"]
        for data in report["pairs"].values()
        for p in data["periods"].values()
        if "missing_rows" in p
    )
    print(f"\nTotal missing rows across pairs/periods: {missing_total}")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
