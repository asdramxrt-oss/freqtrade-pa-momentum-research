"""EXP-003 trade-geometry analysis.

Recomputes the frozen pullback-continuation setup on the spot candles and reports
the geometry of every signal it produces: impulse size, pullback depth (ATR and
percent), pullback duration, distance from the structural origin, and the
continuation-trigger characteristics.

Where the combined full-sample run traded a signal, the trade outcome is joined
back in so the experiment can see *which* pullbacks worked without re-tuning
anything. This is descriptive evidence only.

Usage::

    python user_data/scripts/exp003_geometry.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = PROJECT_ROOT / "user_data" / "strategies" / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from pa_pullback import pullback_continuation_frame  # noqa: E402

SPOT_DIR = PROJECT_ROOT / "user_data" / "data" / "binance"
RAW_RESULTS = PROJECT_ROOT / "research" / "experiment_results" / "EXP-003.raw.json"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "EXP-003.geometry.json"

PAIRS = [
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "ADA",
    "DOGE",
    "LINK",
    "AVAX",
    "DOT",
]

DIRECTIONS = {
    "long": {
        "signal": "long_signal",
        "columns": [
            "impulse_atr_long",
            "pullback_depth_atr_long",
            "pullback_depth_pct_long",
            "pullback_bars_long",
            "dist_from_structure_atr_long",
            "trigger_margin_atr_long",
            "confirm_body_pct_long",
        ],
    },
    "short": {
        "signal": "short_signal",
        "columns": [
            "impulse_atr_short",
            "pullback_depth_atr_short",
            "pullback_depth_pct_short",
            "pullback_bars_short",
            "dist_from_structure_atr_short",
            "trigger_margin_atr_short",
            "confirm_body_pct_short",
        ],
    },
}


def _to_ms(dates: pd.Series) -> pd.Series:
    """
    Convert a datetime series to epoch milliseconds, regardless of resolution.

    :param dates: Datetime series.
    :return: Integer millisecond series.
    """
    converted = pd.to_datetime(dates, utc=True).dt.as_unit("ms")
    return converted.astype("int64")


def _normalise_pair(pair: str) -> str:
    """
    Reduce an exchange pair to its base symbol.

    :param pair: Pair such as ``BTC/USDT:USDT`` or ``BTC/USDT``.
    :return: Base symbol, e.g. ``BTC``.
    """
    return pair.split("/", 1)[0]


def _summary(values: list[float]) -> dict:
    """
    Summarise a numeric list.

    :param values: Finite values.
    :return: Count and distribution summary.
    """
    clean = sorted(float(v) for v in values if v is not None and pd.notna(v))
    if not clean:
        return {"count": 0}
    count = len(clean)

    def percentile(frac: float) -> float:
        """Linear-interpolated percentile."""
        if count == 1:
            return clean[0]
        position = frac * (count - 1)
        lower = int(position)
        upper = min(lower + 1, count - 1)
        weight = position - lower
        return clean[lower] * (1 - weight) + clean[upper] * weight

    return {
        "count": count,
        "mean": sum(clean) / count,
        "median": percentile(0.5),
        "p10": percentile(0.1),
        "p90": percentile(0.9),
    }


def main() -> int:
    """
    Compute and write EXP-003 geometry statistics.

    :return: Process exit code.
    """
    raw = json.loads(RAW_RESULTS.read_text(encoding="utf-8"))
    combined = next(r for r in raw["runs"] if r["label"] == "futures-both-full-0p05")
    outcomes: dict[tuple[str, int, bool], float] = {}
    # Entry tuple layout: [pair, open_ts, close_ts, is_short, profit_abs, exit_reason]
    for entry in combined.get("entry_timestamps", []):
        pair, timestamp, is_short = entry[0], entry[1], entry[3]
        profit = entry[4] if len(entry) > 4 else None
        outcomes[(_normalise_pair(pair), int(timestamp), bool(is_short))] = profit

    records: list[dict] = []
    for symbol in PAIRS:
        candles = pd.read_feather(SPOT_DIR / f"{symbol}_USDT-4h.feather")
        frame = pullback_continuation_frame(
            candles["open"], candles["high"], candles["low"], candles["close"]
        )
        dates = _to_ms(candles["date"])
        exec_ts = dates.shift(-1)
        for direction, spec in DIRECTIONS.items():
            mask = frame[spec["signal"]].fillna(False).astype(bool)
            for index in frame.index[mask]:
                record = {
                    "pair": symbol,
                    "direction": direction,
                    "signal_ts": int(dates.loc[index]),
                    "exec_ts": int(exec_ts.loc[index]) if pd.notna(exec_ts.loc[index]) else None,
                }
                for column in spec["columns"]:
                    value = frame[column].loc[index]
                    record[column] = float(value) if pd.notna(value) else None
                is_short = direction == "short"
                key = (symbol, record["exec_ts"], is_short)
                record["traded"] = key in outcomes
                record["profit_abs"] = outcomes.get(key)
                records.append(record)

    geometry: dict = {"signal_count": len(records), "directions": {}}
    for direction, spec in DIRECTIONS.items():
        subset = [r for r in records if r["direction"] == direction]
        traded = [r for r in subset if r["traded"]]
        winners = [r for r in traded if (r["profit_abs"] or 0) > 0]
        losers = [r for r in traded if (r["profit_abs"] or 0) < 0]
        geometry["directions"][direction] = {
            "signals": len(subset),
            "traded": len(traded),
            "winners": len(winners),
            "losers": len(losers),
            "all": {c: _summary([r[c] for r in subset]) for c in spec["columns"]},
            "winners_mean": {
                c: _summary([r[c] for r in winners]).get("mean") for c in spec["columns"]
            },
            "losers_mean": {
                c: _summary([r[c] for r in losers]).get("mean") for c in spec["columns"]
            },
        }

    geometry["records"] = records
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(geometry, indent=2), encoding="utf-8")

    for direction, data in geometry["directions"].items():
        print(
            f"{direction}: signals={data['signals']} traded={data['traded']} "
            f"winners={data['winners']} losers={data['losers']}"
        )
        for column, stats in data["all"].items():
            print(
                f"    {column:34} mean={stats.get('mean', float('nan')):.3f} "
                f"median={stats.get('median', float('nan')):.3f}"
            )
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
