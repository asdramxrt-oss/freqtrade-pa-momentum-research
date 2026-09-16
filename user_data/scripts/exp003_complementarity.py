"""EXP-003 complementarity preparation (descriptive only).

Compares the pullback-continuation entries against the reference breakout
baseline, purely to leave structured evidence for a *future* combination
experiment. Nothing here changes the strategy, and no combination is built.

Reported per comparison:

* exact entry overlap (same pair and same 4h bar),
* near overlap (same pair within 24h),
* calendar-day entry overlap,
* simultaneous exposure (both strategies holding a position on the same pair/day),
* daily-return correlation,
* drawdown correlation.

Usage::

    python user_data/scripts/exp003_complementarity.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_RESULTS = PROJECT_ROOT / "research" / "experiment_results" / "EXP-003.raw.json"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "EXP-003.complementarity.json"

NEAR_WINDOW_MS = 24 * 60 * 60 * 1000  # 24 hours

# Entry tuple layout: [pair, open_ts, close_ts, is_short, profit_abs, exit_reason]


def _base_symbol(pair: str) -> str:
    """
    Reduce an exchange pair to its base symbol.

    :param pair: Pair such as ``BTC/USDT:USDT``.
    :return: Base symbol.
    """
    return pair.split("/", 1)[0]


def _day(ms: int) -> str:
    """
    Convert epoch milliseconds to an ISO date string.

    :param ms: Epoch milliseconds.
    :return: ``YYYY-MM-DD`` string.
    """
    return pd.Timestamp(int(ms), unit="ms", tz="UTC").strftime("%Y-%m-%d")


def _daily_pnl(entries: list[list]) -> pd.Series:
    """
    Build a daily realised-PnL series from trade entries.

    :param entries: Entry tuples.
    :return: Series indexed by ISO date.
    """
    if not entries:
        return pd.Series(dtype=float)
    frame = pd.DataFrame(
        {"day": [_day(e[2]) for e in entries], "pnl": [float(e[4]) for e in entries]}
    )
    return frame.groupby("day")["pnl"].sum().sort_index()


def _drawdown(series: pd.Series) -> pd.Series:
    """
    Drawdown from the running maximum of a cumulative series.

    :param series: Cumulative PnL series.
    :return: Drawdown series (<= 0).
    """
    running_max = series.cummax()
    return series - running_max


def _exposure_pairs(entries: list[list]) -> set[tuple[str, str]]:
    """
    Set of (base symbol, day) touched by any open position.

    :param entries: Entry tuples.
    :return: Set of symbol/day pairs.
    """
    touched: set[tuple[str, str]] = set()
    for entry in entries:
        symbol = _base_symbol(entry[0])
        days = pd.date_range(
            pd.Timestamp(int(entry[1]), unit="ms", tz="UTC").floor("D"),
            pd.Timestamp(int(entry[2]), unit="ms", tz="UTC").floor("D"),
            freq="D",
        )
        for day in days:
            touched.add((symbol, day.strftime("%Y-%m-%d")))
    return touched


def compare(name: str, entries_a: list[list], entries_b: list[list]) -> dict:
    """
    Compute descriptive complementarity statistics.

    :param name: Label for the comparison.
    :param entries_a: Pullback entries.
    :param entries_b: Baseline entries.
    :return: Statistics dictionary.
    """
    keys_a = {(_base_symbol(e[0]), int(e[1])) for e in entries_a}
    keys_b = {(_base_symbol(e[0]), int(e[1])) for e in entries_b}
    exact = keys_a & keys_b

    near = 0
    by_symbol: dict[str, list[int]] = {}
    for symbol, ts in keys_b:
        by_symbol.setdefault(symbol, []).append(ts)
    for symbol, ts in keys_a:
        candidates = by_symbol.get(symbol, [])
        if any(abs(ts - other) <= NEAR_WINDOW_MS for other in candidates):
            near += 1

    days_a = {_day(e[1]) for e in entries_a}
    days_b = {_day(e[1]) for e in entries_b}

    exposure_a = _exposure_pairs(entries_a)
    exposure_b = _exposure_pairs(entries_b)
    exposure_union = exposure_a | exposure_b

    pnl_a = _daily_pnl(entries_a)
    pnl_b = _daily_pnl(entries_b)
    aligned = pd.concat([pnl_a.rename("a"), pnl_b.rename("b")], axis=1).fillna(0.0)

    corr = aligned["a"].corr(aligned["b"]) if len(aligned) > 2 else None
    cumulative = aligned.cumsum()
    dd_a = _drawdown(cumulative["a"])
    dd_b = _drawdown(cumulative["b"])
    dd_corr = dd_a.corr(dd_b) if len(aligned) > 2 else None

    return {
        "comparison": name,
        "pullback_trades": len(entries_a),
        "baseline_trades": len(entries_b),
        "exact_entry_overlap": len(exact),
        "exact_overlap_pct_of_pullback": (len(exact) / len(keys_a) * 100) if keys_a else None,
        "near_entry_overlap_within_24h": near,
        "near_overlap_pct_of_pullback": (near / len(keys_a) * 100) if keys_a else None,
        "entry_day_overlap": len(days_a & days_b),
        "entry_day_overlap_pct_of_pullback": (len(days_a & days_b) / len(days_a) * 100)
        if days_a
        else None,
        "exposure_pairday_jaccard": (len(exposure_a & exposure_b) / len(exposure_union))
        if exposure_union
        else None,
        "daily_return_correlation": float(corr) if corr is not None and pd.notna(corr) else None,
        "drawdown_correlation": float(dd_corr)
        if dd_corr is not None and pd.notna(dd_corr)
        else None,
        "pullback_days": len(pnl_a),
        "baseline_days": len(pnl_b),
    }


def main() -> int:
    """
    Compute and write the complementarity preparation.

    :return: Process exit code.
    """
    raw = json.loads(RAW_RESULTS.read_text(encoding="utf-8"))
    runs = {r["label"]: r for r in raw["runs"]}

    turtle = runs["turtle-spot-long-full"]["entry_timestamps"]
    combined = runs["futures-both-full-0p05"]["entry_timestamps"]
    spot_long = runs["spot-long-full"]["entry_timestamps"]

    output = {
        "experiment_id": "EXP-003",
        "note": (
            "Descriptive preparation only. No combination is built and nothing is "
            "optimised from these numbers."
        ),
        "comparisons": [
            compare("pullback_combined_futures_vs_turtle_spot", combined, turtle),
            compare("pullback_long_spot_vs_turtle_spot", spot_long, turtle),
        ],
    }
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")

    for item in output["comparisons"]:
        print(json.dumps(item, indent=2))
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
