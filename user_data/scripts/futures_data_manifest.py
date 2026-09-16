"""Build the Phase-3 genuine-futures data manifest.

Scans the separate Phase-3 datadir (default ``user_data/data_p3``) and records
row counts, coverage, duplicates, gaps, timezone, schema and SHA-256 checksums
for every stored candle file. Read-only: it never writes into the data directory
and never touches the historical spot mirror at ``user_data/data``.

Usage::

    python user_data/scripts/futures_data_manifest.py
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_P3 = PROJECT_ROOT / "user_data" / "data_p3"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "P3_FUTURES_DATA_MANIFEST.json"
MIRROR = PROJECT_ROOT / "user_data" / "data" / "binance" / "futures"

NAME_RE = re.compile(
    r"^(?P<pair>[A-Z0-9]+_USDT_USDT)-(?P<tf>\d+[a-z])-(?P<type>[a-zA-Z_]+)\.feather$"
)
STEP = pd.Timedelta(hours=4)


def sha256(path: Path) -> str:
    """
    SHA-256 of a file.

    :param path: File path.
    :return: Hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe(path: Path) -> dict:
    """
    Summarise one stored candle file.

    :param path: Feather file.
    :return: Per-file manifest entry.
    """
    match = NAME_RE.match(path.name)
    frame = pd.read_feather(path)
    dates = pd.to_datetime(frame["date"], utc=True)
    gaps = dates.diff().dropna()
    on_4h_grid = bool(match and match.group("tf") == "4h")
    expected = (
        int((dates.iloc[-1] - dates.iloc[0]) / STEP) + 1 if on_4h_grid and len(dates) > 1 else None
    )
    return {
        "file": path.name,
        "pair": match.group("pair").replace("_USDT_USDT", "/USDT:USDT") if match else None,
        "timeframe": match.group("tf") if match else None,
        "candle_type": match.group("type") if match else None,
        "columns": list(frame.columns),
        "rows": int(len(frame)),
        "first": str(dates.iloc[0]) if len(dates) else None,
        "last": str(dates.iloc[-1]) if len(dates) else None,
        "duplicate_timestamps": int(dates.duplicated().sum()),
        "is_monotonic_increasing": bool(dates.is_monotonic_increasing),
        "timezone_aware_utc": bool(str(dates.dt.tz) == "UTC"),
        "on_uniform_grid": on_4h_grid,
        "expected_rows_on_4h_grid": expected,
        "missing_rows": (expected - int(len(dates))) if expected is not None else None,
        "gaps_gt_one_step": int((gaps > STEP).sum()) if on_4h_grid and len(gaps) else None,
        "median_gap_hours": float(gaps.median() / pd.Timedelta(hours=1)) if len(gaps) else None,
        "max_gap_hours": float(gaps.max() / pd.Timedelta(hours=1)) if len(gaps) else 0.0,
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def main() -> int:
    """
    Build and write the manifest.

    :return: Process exit code.
    """
    if not DATA_P3.exists():
        raise SystemExit(f"Phase-3 datadir not found: {DATA_P3}")

    files = sorted(DATA_P3.rglob("*.feather"))
    entries = [describe(path) for path in files]

    by_type: dict[str, list[dict]] = {}
    for entry in entries:
        by_type.setdefault(entry["candle_type"] or "unknown", []).append(entry)

    summary = {
        candle_type: {
            "files": len(items),
            "total_rows": sum(i["rows"] for i in items),
            "duplicate_timestamps": sum(i["duplicate_timestamps"] for i in items),
            "missing_rows": (
                sum(i["missing_rows"] for i in items if i["missing_rows"] is not None)
                if items[0]["on_uniform_grid"]
                else "n/a (not on a uniform 4h grid)"
            ),
            "earliest": min((i["first"] for i in items if i["first"]), default=None),
            "latest": max((i["last"] for i in items if i["last"]), default=None),
        }
        for candle_type, items in sorted(by_type.items())
    }

    manifest = {
        "manifest": "P3 natural genuine Binance USDT-M futures dataset",
        "generated_utc": datetime.now(UTC).isoformat(),
        "datadir": str(DATA_P3.relative_to(PROJECT_ROOT)),
        "exchange": "binance",
        "market_type": "USDT-margined perpetual futures",
        "symbols": sorted({e["pair"] for e in entries if e["pair"]}),
        "timeframe": "4h (funding_rate stored on a 1h container, one row per funding event)",
        "data_source_api": "Binance USDⓈ-M futures via freqtrade download-data + ccxt",
        "timestamp_convention": "candle OPEN time, epoch milliseconds, injected as tz-aware UTC by freqtrade",
        "timezone": "UTC",
        "schema": {
            "ohlcv": ["date", "open", "high", "low", "close", "volume"],
            "funding_rate": "date + funding rate/interval columns as stored by freqtrade",
        },
        "transformation_history": [
            "downloaded with user_data/scripts/download_futures_data.ps1 (no local transformation)",
            "no resampling, no fill, no adjustment applied",
        ],
        "separate_from_spot_mirror": {
            "spot_mirror_datadir": str(MIRROR.relative_to(PROJECT_ROOT)),
            "note": "the spot mirror is a byte-identical copy of spot candles and is NOT genuine futures OHLCV",
        },
        "summary_by_candle_type": summary,
        "files": entries,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"{'type':14} {'files':>5} {'rows':>8} {'dups':>5} {'missing':>7}  earliest -> latest")
    for candle_type, data in summary.items():
        print(
            f"{candle_type:14} {data['files']:>5} {data['total_rows']:>8} "
            f"{data['duplicate_timestamps']:>5} {data['missing_rows']:>7}  "
            f"{str(data['earliest'])[:19]} -> {str(data['latest'])[:19]}"
        )
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
