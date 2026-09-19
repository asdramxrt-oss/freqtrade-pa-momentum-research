"""One-shot governed runner for P3-EXP-004B residual momentum.

The runner never changes the gate and never promotes production code.
It requires PHASE3 authorization and blocks repeat execution with a completion marker.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER_DATA = ROOT / "user_data"
CONFIG = USER_DATA / "configs" / "P3-EXP-004B.json"
STRATEGY_DIR = ROOT / "research_lib" / "strategies"
STRATEGY_FILE = STRATEGY_DIR / "ResidualMomentumResearch.py"
GATE = ROOT / ".mece" / "PHASE_GATE.json"
RUNS = ROOT / "phase_runs" / "p3_exp004b"
DATA = USER_DATA / "data_p3"
COMPLETION = RUNS / "P3-EXP-004B_COMPLETED.json"
TIMERANGE = "20190101-20260916"
SLICES = {
    "full_sample": "20190101-20260916",
    "train": "20190101-20221231",
    "validation": "20230101-20241231",
    "oos": "20250101-20260916",
}
FEE = 0.0005
STRATEGY = "ResidualMomentum"
PAIRS = [
    "BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT",
    "SOL/USDT:USDT", "XRP/USDT:USDT", "ADA/USDT:USDT",
    "DOGE/USDT:USDT", "LINK/USDT:USDT", "AVAX/USDT:USDT",
    "DOT/USDT:USDT",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def gate() -> dict:
    g = json.loads(GATE.read_text(encoding="utf-8"))
    if g.get("phase") != "PHASE3" or not g.get("allow_new_experiments") or g.get("stop_after_phase_completion"):
        raise RuntimeError("P3-EXP-004B is not authorized by the PHASE3 gate.")
    return g


def data_files() -> list[Path]:
    return [
        DATA / f"{p.replace('/', '_').replace(':', '_')}-4h-futures.feather"
        for p in PAIRS
    ]


def download_if_needed() -> None:
    missing = [p for p in data_files() if not p.exists() or p.stat().st_size == 0]
    if not missing:
        return
    cmd = [
        sys.executable, "-m", "freqtrade", "download-data",
        "--userdir", str(USER_DATA), "-d", str(DATA), "-c", str(CONFIG),
        "-t", "4h", "--trading-mode", "futures", "--candle-types", "futures",
        "--timerange", TIMERANGE,
    ]
    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    log = RUNS / f"download_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.log"
    log.write_text("$ " + " ".join(cmd) + "\n\nSTDOUT\n" + cp.stdout + "\nSTDERR\n" + cp.stderr, encoding="utf-8")
    if cp.returncode != 0:
        raise RuntimeError(f"Futures download failed; see {log}")
    missing = [p for p in data_files() if not p.exists() or p.stat().st_size == 0]
    if missing:
        raise RuntimeError("Required genuine futures files are missing: " + "; ".join(map(str, missing)))


def latest_export() -> Path:
    pointer = USER_DATA / "backtest_results" / ".last_result.json"
    if not pointer.exists():
        raise RuntimeError("Freqtrade did not produce .last_result.json")
    latest = json.loads(pointer.read_text(encoding="utf-8")).get("latest_backtest")
    if not latest:
        raise RuntimeError("latest_backtest missing")
    path = USER_DATA / "backtest_results" / latest
    if not path.exists():
        raise RuntimeError(f"Backtest export missing: {path}")
    return path


def read_export(path: Path) -> dict:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            members = [n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
            if not members:
                raise RuntimeError("No JSON result in backtest zip")
            return json.loads(z.read(members[0]))
    return json.loads(path.read_text(encoding="utf-8"))


def run_slice(label: str, timerange: str, base_cmd: list[str]) -> dict:
    cmd = list(base_cmd)
    i = cmd.index("--timerange")
    cmd[i + 1] = timerange
    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    log = RUNS / f"{label}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.log"
    log.write_text("$ " + " ".join(cmd) + "\n\nSTDOUT\n" + cp.stdout + "\nSTDERR\n" + cp.stderr, encoding="utf-8")
    if cp.returncode != 0:
        raise RuntimeError(f"{label} backtest failed; see {log}")
    export = latest_export()
    return {"timerange": timerange, "export": str(export.relative_to(ROOT)), "log": str(log.relative_to(ROOT)), "result": read_export(export)}


def main() -> int:
    RUNS.mkdir(parents=True, exist_ok=True)
    if COMPLETION.exists():
        print("P3-EXP-004B already executed once; repeat evaluation is blocked.")
        return 0

    g = gate()
    for p in [CONFIG, STRATEGY_FILE, GATE]:
        if not p.exists():
            raise RuntimeError(f"Missing required file: {p}")

    download_if_needed()

    before = {
        "gate": g,
        "strategy_sha256": sha256(STRATEGY_FILE),
        "config_sha256": sha256(CONFIG),
        "frozen_spec_sha256": sha256(ROOT / "docs" / "FROZEN_IMPLEMENTATION_SPEC.md"),
        "started_utc": datetime.now(UTC).isoformat(),
    }

    base = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--userdir", str(USER_DATA), "--strategy-path", str(STRATEGY_DIR),
        "-c", str(CONFIG), "--strategy", STRATEGY, "-d", str(DATA),
        "--timerange", TIMERANGE, "--cache", "none", "--export", "trades",
        "--fee", repr(FEE),
    ]

    print("P3-EXP-004B AUTHORIZED — executing exactly one preregistered evaluation.")
    slices = {name: run_slice(name, timerange, base) for name, timerange in SLICES.items()}

    after_gate = json.loads(GATE.read_text(encoding="utf-8"))
    after = {
        "gate": after_gate,
        "strategy_sha256": sha256(STRATEGY_FILE),
        "config_sha256": sha256(CONFIG),
        "frozen_spec_sha256": sha256(ROOT / "docs" / "FROZEN_IMPLEMENTATION_SPEC.md"),
        "completed_utc": datetime.now(UTC).isoformat(),
    }

    raw = RUNS / f"P3-EXP-004B_RAW_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        "experiment_id": "P3-EXP-004B",
        "status": "EXECUTED",
        "diagnostic_only": False,
        "live_trading": False,
        "promotion": False,
        "preregistered_slices": SLICES,
        "fee_per_side": FEE,
        "strategy": STRATEGY,
        "config": str(CONFIG.relative_to(ROOT)),
        "strategy_path": str(STRATEGY_FILE.relative_to(ROOT)),
        "data_directory": str(DATA.relative_to(ROOT)),
        "data_files": [str(p.relative_to(ROOT)) for p in data_files()],
        "integrity_before": before,
        "integrity_after": after,
        "slice_results": slices,
        "cost_note": "Base fee only in this runner. Freqtrade backtesting does not natively apply slippage; stress slippage remains a required downstream diagnostic and is not inferred here.",
    }
    raw.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    COMPLETION.write_text(json.dumps({
        "experiment_id": "P3-EXP-004B",
        "executed_utc": after["completed_utc"],
        "raw_result": str(raw.relative_to(ROOT)),
        "promotion": False,
    }, indent=2), encoding="utf-8")
    print(f"RAW RESULT: {raw}")
    print("P3-EXP-004B EXECUTION FINISHED.")
    print("Promotion remains FALSE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
