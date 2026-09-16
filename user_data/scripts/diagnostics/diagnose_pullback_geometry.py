"""PHASE 2 diagnostic: pullback geometry and post-signal behaviour by period.

Uses the frozen ``pullback_continuation_frame`` (read-only) to describe the long
setup's geometry and its forward excursions across development / 2025 / 2026, and
to re-test the EXP-003 finding that winners and losers are geometrically similar.
No rule is created or changed.

Usage::

    python user_data/scripts/diagnostics/diagnose_pullback_geometry.py
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
from pa_pullback import pullback_continuation_frame  # noqa: E402

OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_pullback_geometry.json"
GEOMETRY = [
    "impulse_atr_long",
    "pullback_depth_atr_long",
    "pullback_depth_pct_long",
    "pullback_bars_long",
    "dist_from_structure_atr_long",
    "trigger_margin_atr_long",
    "confirm_body_pct_long",
]
HORIZONS = [6, 12, 24, 48]


def _signals_for_pair(symbol: str) -> pd.DataFrame:
    """
    Long pullback signals with geometry and forward excursions for one pair.

    :param symbol: Base symbol.
    :return: DataFrame indexed by bar with signal flags and columns.
    """
    frame = load_candles(symbol)
    setup = pullback_continuation_frame(frame["open"], frame["high"], frame["low"], frame["close"])
    out = setup[GEOMETRY].copy()
    out["date"] = frame["date"]
    out["signal"] = setup["long_signal"].fillna(False).astype(bool)
    out["atr_pct"] = setup["atr"] / frame["close"]
    for horizon in HORIZONS:
        excursions = forward_excursions(frame["close"], frame["high"], frame["low"], horizon)
        out[f"fwd_ret_{horizon}"] = excursions["fwd_ret"]
        out[f"mfe_{horizon}"] = excursions["mfe"]
        out[f"mae_{horizon}"] = excursions["mae"]
        out[f"fwd_ret_{horizon}_atr"] = excursions["fwd_ret"] / out["atr_pct"]
        out[f"mfe_{horizon}_atr"] = excursions["mfe"] / out["atr_pct"]
        out[f"mae_{horizon}_atr"] = excursions["mae"] / out["atr_pct"]
    return out


def main() -> int:
    """
    Run the pullback geometry diagnostic and write the result.

    :return: Process exit code.
    """
    per_pair = {symbol: _signals_for_pair(symbol) for symbol in PAIRS}

    # Market-relative forward returns: subtract the equal-weight universe forward
    # return over the same horizon, to separate setup behaviour from market beta.
    universe = {}
    for horizon in HORIZONS:
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
        for horizon in HORIZONS:
            data[f"excess_{horizon}"] = (
                data[f"fwd_ret_{horizon}"].to_numpy() - universe[horizon].reindex(dates).to_numpy()
            )

    output = {
        "phase": "PHASE2",
        "generated_utc": datetime.now(UTC).isoformat(),
        "periods": {},
    }

    fwd_cols = (
        [f"fwd_ret_{h}" for h in HORIZONS]
        + [f"mfe_{h}" for h in HORIZONS]
        + [f"mae_{h}" for h in HORIZONS]
        + [f"fwd_ret_{h}_atr" for h in HORIZONS]
        + [f"mfe_{h}_atr" for h in HORIZONS]
        + [f"mae_{h}_atr" for h in HORIZONS]
        + [f"excess_{h}" for h in HORIZONS]
    )

    for period, (start, end) in PERIODS.items():
        collected = []
        for symbol, data in per_pair.items():
            dates = pd.to_datetime(data["date"], utc=True)
            mask = (dates >= pd.Timestamp(start, tz="UTC")) & (dates < pd.Timestamp(end, tz="UTC"))
            signals = data.loc[mask & data["signal"]].copy()
            if not signals.empty:
                signals["pair"] = symbol
                collected.append(signals)
        pooled = pd.concat(collected, ignore_index=True) if collected else pd.DataFrame()
        entry: dict = {"signals": int(len(pooled))}
        if not pooled.empty:
            entry["geometry_median"] = {
                column: summarize(pooled[column])["median"] for column in GEOMETRY
            }
            entry["forward_median"] = {
                column: summarize(pooled[column])["median"] for column in fwd_cols
            }
            entry["forward_mean"] = {
                column: summarize(pooled[column])["mean"]
                for column in (
                    [f"fwd_ret_{h}" for h in HORIZONS]
                    + [f"fwd_ret_{h}_atr" for h in HORIZONS]
                    + [f"excess_{h}" for h in HORIZONS]
                )
            }
            winners = pooled.loc[pooled["fwd_ret_24"] > 0]
            losers = pooled.loc[pooled["fwd_ret_24"] <= 0]
            entry["winners"] = int(len(winners))
            entry["losers"] = int(len(losers))
            entry["geometry_median_winners"] = {
                column: summarize(winners[column])["median"] for column in GEOMETRY
            }
            entry["geometry_median_losers"] = {
                column: summarize(losers[column])["median"] for column in GEOMETRY
            }
            entry["forward_median_winners"] = {
                column: summarize(winners[column])["median"] for column in fwd_cols
            }
            entry["forward_median_losers"] = {
                column: summarize(losers[column])["median"] for column in fwd_cols
            }
        output["periods"][period] = entry

    write_json(OUTPUT, output)

    print("Pullback long: geometry medians and forward behaviour")
    for period in ("D_development", "C_consumed_2025", "F_fresh_2026"):
        entry = output["periods"][period]
        print(
            f"\n== {period}  signals={entry['signals']} "
            f"W/L={entry.get('winners')}/{entry.get('losers')}"
        )
        if "geometry_median" not in entry:
            continue
        for column in GEOMETRY:
            print(f"   geom {column:32} {entry['geometry_median'][column]:>9.4f}")
        for column in (
            "fwd_ret_24",
            "mfe_24",
            "mae_24",
            "fwd_ret_24_atr",
            "mfe_24_atr",
            "excess_24",
        ):
            print(f"   fwd  {column:32} {entry['forward_median'][column]:>9.4f}")
        print(
            f"   mean fwd_ret_24={entry['forward_mean']['fwd_ret_24']:>9.4f}  "
            f"mean excess_24={entry['forward_mean']['excess_24']:>9.4f}  "
            f"mean excess_6={entry['forward_mean']['excess_6']:>9.4f}"
        )
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
