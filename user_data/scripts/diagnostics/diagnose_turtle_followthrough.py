"""PHASE 2 diagnostic: Turtle breakout follow-through by period.

Uses the frozen Donchian signal definition (read-only) to ask whether breakouts
were followed by less continuation in 2026 than in earlier periods. No rule is
changed and no threshold is derived.

Usage::

    python user_data/scripts/diagnostics/diagnose_turtle_followthrough.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diag_common import (  # noqa: E402
    PAIRS,
    PERIODS,
    PROJECT_ROOT,
    forward_excursions,
    load_candles,
    summarize,
    write_json,
)
from pa_indicators import atr  # noqa: E402
from pa_signals import donchian_breakout_frame  # noqa: E402

OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_turtle_followthrough.json"
HORIZONS = [1, 3, 6, 12, 24, 48]
NORMALISED = [3, 6, 24, 48]


def _signals_for_pair(symbol: str) -> pd.DataFrame:
    """
    Breakout signals with forward excursions for one pair (whole file).

    :param symbol: Base symbol.
    :return: DataFrame with ``date``, ``first_breakout_up`` and forward columns.
    """
    frame = load_candles(symbol)
    breakout = donchian_breakout_frame(
        frame["high"], frame["low"], frame["close"], entry_period=20, exit_period=10
    )
    atr_pct = atr(frame["high"], frame["low"], frame["close"], 20) / frame["close"]
    out = pd.DataFrame(
        {"date": frame["date"], "signal": breakout["first_breakout_up"], "atr_pct": atr_pct}
    )
    for horizon in HORIZONS:
        excursions = forward_excursions(frame["close"], frame["high"], frame["low"], horizon)
        out[f"fwd_ret_{horizon}"] = excursions["fwd_ret"]
        out[f"mfe_{horizon}"] = excursions["mfe"]
        out[f"mae_{horizon}"] = excursions["mae"]
    # ATR-normalised follow-through: the strategy risks a fixed 2*ATR, so
    # ATR-relative movement is the vol-neutral comparison.
    for horizon in NORMALISED:
        out[f"fwd_ret_{horizon}_atr"] = out[f"fwd_ret_{horizon}"] / out["atr_pct"]
        out[f"mfe_{horizon}_atr"] = out[f"mfe_{horizon}"] / out["atr_pct"]
        out[f"mae_{horizon}_atr"] = out[f"mae_{horizon}"] / out["atr_pct"]
    return out


def main() -> int:
    """
    Run the follow-through diagnostic and write the result.

    :return: Process exit code.
    """
    per_pair = {symbol: _signals_for_pair(symbol) for symbol in PAIRS}

    # Market-relative forward returns (equal-weight universe) to separate
    # breakout behaviour from market beta.
    universe = {}
    for horizon in NORMALISED:
        series = {
            symbol: pd.Series(
                data[f"fwd_ret_{horizon}"].to_numpy(),
                index=pd.to_datetime(data["date"], utc=True),
            )
            for symbol, data in per_pair.items()
        }
        universe[horizon] = pd.DataFrame(series).mean(axis=1, skipna=True)
    for data in per_pair.values():
        dates = pd.to_datetime(data["date"], utc=True)
        for horizon in NORMALISED:
            data[f"excess_{horizon}"] = (
                data[f"fwd_ret_{horizon}"].to_numpy() - universe[horizon].reindex(dates).to_numpy()
            )

    output = {
        "phase": "PHASE2",
        "generated_utc": datetime.now(UTC).isoformat(),
        "per_pair": {},
        "aggregate": {},
    }

    for symbol, data in per_pair.items():
        output["per_pair"][symbol] = {}
        for period, (start, end) in PERIODS.items():
            dates = pd.to_datetime(data["date"], utc=True)
            mask = (dates >= pd.Timestamp(start, tz="UTC")) & (dates < pd.Timestamp(end, tz="UTC"))
            signals = data.loc[mask & data["signal"]]
            entry = {
                "signals": int(len(signals)),
                "immediate_fail_1bar": float((signals["fwd_ret_1"] < 0).mean())
                if len(signals)
                else None,
            }
            for horizon in HORIZONS:
                entry[f"fwd_ret_{horizon}_mean"] = float(signals[f"fwd_ret_{horizon}"].mean())
                entry[f"mfe_{horizon}_mean"] = float(signals[f"mfe_{horizon}"].mean())
                entry[f"mae_{horizon}_mean"] = float(signals[f"mae_{horizon}"].mean())
            for horizon in NORMALISED:
                entry[f"fwd_ret_{horizon}_atr_mean"] = float(
                    signals[f"fwd_ret_{horizon}_atr"].mean()
                )
                entry[f"mfe_{horizon}_atr_mean"] = float(signals[f"mfe_{horizon}_atr"].mean())
                entry[f"mae_{horizon}_atr_mean"] = float(signals[f"mae_{horizon}_atr"].mean())
            for horizon in NORMALISED:
                entry[f"excess_{horizon}_mean"] = float(signals[f"excess_{horizon}"].mean())
            output["per_pair"][symbol][period] = entry

    horizons_keys = (
        [f"fwd_ret_{h}_mean" for h in HORIZONS]
        + [f"mfe_{h}_mean" for h in HORIZONS]
        + [f"mae_{h}_mean" for h in HORIZONS]
        + [f"fwd_ret_{h}_atr_mean" for h in NORMALISED]
        + [f"mfe_{h}_atr_mean" for h in NORMALISED]
        + [f"mae_{h}_atr_mean" for h in NORMALISED]
        + [f"excess_{h}_mean" for h in NORMALISED]
    )
    for period in PERIODS:
        rows = [p[period] for p in output["per_pair"].values() if p[period]["signals"] > 0]
        aggregate = {
            "signals_total": int(sum(r["signals"] for r in rows)),
            "immediate_fail_1bar_mean": summarize(
                [r["immediate_fail_1bar"] for r in rows if r["immediate_fail_1bar"] is not None]
            )["median"]
            if rows
            else None,
        }
        for key in horizons_keys:
            aggregate[key] = summarize([r[key] for r in rows])["median"] if rows else None
        output["aggregate"][period] = aggregate

    write_json(OUTPUT, output)

    print("Turtle breakout follow-through (median across pairs)")
    print(f"{'metric':20} {'D_dev':>10} {'C_2025':>10} {'F_2026':>10}")
    for key in ["signals_total", "immediate_fail_1bar_mean"] + horizons_keys:
        row = [
            output["aggregate"][p].get(key)
            for p in ("D_development", "C_consumed_2025", "F_fresh_2026")
        ]
        if key == "signals_total":
            print(f"{key:20} {row[0]:>10} {row[1]:>10} {row[2]:>10}")
        else:
            print(f"{key:20} {row[0]:>10.5f} {row[1]:>10.5f} {row[2]:>10.5f}")
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
