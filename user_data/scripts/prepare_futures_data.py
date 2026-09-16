"""Mirror the spot OHLCV dataset into a futures dataset for EXP-003.

freqtrade cannot express short trades in spot mode, and the ``binance`` exchange
supports only spot and futures (margin is unavailable). To keep EXP-003 on the
*exact same candles* as EXP-001/EXP-002, this script copies every
``user_data/data/binance/<PAIR>-4h.feather`` to
``user_data/data/binance/futures/<BASE>_<QUOTE>_<QUOTE>-4h-futures.feather`` with
byte-identical OHLCV.

Consequences (documented in ``research/experiment_specs/EXP-003.md`` §6):

* The futures backtest sees the same underlying candles as the spot runs, so the
  entry logic is isolated from basis and funding effects.
* No funding-rate data exists, so funding is excluded from all EXP-003 results.
* The spot long-only control quantifies the mode deviation for the long side.

Usage::

    python user_data/scripts/prepare_futures_data.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPOT_DIR = PROJECT_ROOT / "user_data" / "data" / "binance"
FUTURES_DIR = SPOT_DIR / "futures"


def futures_filename(spot_name: str) -> str:
    """
    Convert a spot OHLCV filename into its futures-mirror filename.

    ``BTC_USDT-4h.feather`` -> ``BTC_USDT_USDT-4h-futures.feather``

    :param spot_name: Spot filename stem with extension.
    :return: Futures filename.
    """
    stem = spot_name.removesuffix(".feather")
    pair, timeframe = stem.rsplit("-", 1)
    base, quote = pair.split("_", 1)
    return f"{base}_{quote}_{quote}-{timeframe}-futures.feather"


def main() -> int:
    """
    Mirror every spot 4h feather file into the futures directory.

    :return: Process exit code.
    """
    FUTURES_DIR.mkdir(parents=True, exist_ok=True)
    sources = sorted(SPOT_DIR.glob("*-4h.feather"))
    if not sources:
        raise SystemExit(f"no spot feather files found in {SPOT_DIR}")

    for source in sources:
        target = FUTURES_DIR / futures_filename(source.name)
        frame = pd.read_feather(source)
        frame.to_feather(target)
        print(f"{source.name} -> {target.relative_to(PROJECT_ROOT)}  ({len(frame)} rows)")
    print(f"\nMirrored {len(sources)} pairs into {FUTURES_DIR.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
