from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER_DATA = ROOT / "user_data"
CONFIG = USER_DATA / "configs" / "P3-EXP-004A.json"
STRATEGY_DIR = ROOT / "research_lib" / "strategies"
STRATEGY_FILE = STRATEGY_DIR / "CrossSectionalMomentumResearch.py"
GATE = ROOT / ".mece" / "PHASE_GATE.json"
RESULTS = ROOT / "research" / "experiment_results"
RUNS = ROOT / "phase_runs" / "p3_exp004a"
DATA = USER_DATA / "data_p3"
TIMERANGE = "20190101-20260916"
FEE = 0.0005
STRATEGY = "CrossSectionalMomentum"

PAIRS = [
    "BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT",
    "SOL/USDT:USDT", "XRP/USDT:USDT", "ADA/USDT:USDT",
    "DOGE/USDT:USDT", "LINK/USDT:USDT", "AVAX/USDT:USDT",
    "DOT/USDT:USDT",
]

def sha256(path: Path) -> str:
    h = __import__("hashlib").sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_gate() -> dict:
    data = json.loads(GATE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("PHASE_GATE.json is not an object")
    if not isinstance(data.get("allow_new_experiments"), bool):
        raise RuntimeError("allow_new_experiments is not boolean")
    if not isinstance(data.get("stop_after_phase_completion"), bool):
        raise RuntimeError("stop_after_phase_completion is not boolean")
    return data

def authorized(g: dict) -> bool:
    return bool(g["allow_new_experiments"]) and not bool(g["stop_after_phase_completion"])

def find_export() -> Path:
    pointer = USER_DATA / "backtest_results" / ".last_result.json"
    if not pointer.exists():
        raise RuntimeError("Freqtrade did not produce .last_result.json")
    p = json.loads(pointer.read_text(encoding="utf-8"))
    latest = p.get("latest_backtest")
    if not latest:
        raise RuntimeError("latest_backtest missing from .last_result.json")
    path = USER_DATA / "backtest_results" / latest
    if not path.exists():
        raise RuntimeError(f"backtest export not found: {path}")
    return path

def read_export(path: Path) -> dict:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            members = [
                n for n in z.namelist()
                if n.endswith(".json") and not n.endswith("_config.json")
            ]
            if not members:
                raise RuntimeError("No JSON backtest result inside export zip")
            return json.loads(z.read(members[0]))
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    RUNS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    g = load_gate()
    if not authorized(g):
        print("P3-EXP-004A RUNNER: WAIT")
        print(f"phase={g.get('phase')}")
        print(f"allow_new_experiments={g['allow_new_experiments']}")
        print(f"stop_after_phase_completion={g['stop_after_phase_completion']}")
        print("No experiment executed.")
        return 0

    required = [CONFIG, STRATEGY_FILE, GATE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Missing required files: " + "; ".join(missing))

    def futures_file(pair: str) -> Path:
        stem = pair.replace("/", "_").replace(":", "_")
        return DATA / f"{stem}-4h-futures.feather"

    data_files = [futures_file(p) for p in PAIRS]
    missing_data = [p for p in data_files if not p.exists()]
    if missing_data:
        print("Genuine Phase-3 futures data missing; downloading into data_p3 (spot mirror untouched).")
        download = [
            sys.executable, "-m", "freqtrade", "download-data",
            "--userdir", str(USER_DATA),
            "-d", str(DATA),
            "-c", str(CONFIG),
            "-t", "4h",
            "--trading-mode", "futures",
            "--candle-types", "futures",
            "--timerange", TIMERANGE,
        ]
        cp_download = subprocess.run(
            download, cwd=str(ROOT), capture_output=True, text=True, check=False
        )
        download_log = RUNS / f"p3_exp004a_download_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.log"
        download_log.write_text(
            "$ " + " ".join(download) + "\n\nSTDOUT\n" + cp_download.stdout +
            "\nSTDERR\n" + cp_download.stderr, encoding="utf-8"
        )
        if cp_download.returncode != 0:
            raise RuntimeError(f"Genuine futures download failed; see {download_log}")
        missing_data = [p for p in data_files if not p.exists()]
        if missing_data:
            raise RuntimeError("Genuine futures files still missing after download: " + "; ".join(map(str, missing_data)))

    # Freeze integrity inputs immediately before execution.
    before = {
        "gate": g,
        "strategy_sha256": sha256(STRATEGY_FILE),
        "config_sha256": sha256(CONFIG),
        "frozen_spec_sha256": sha256(ROOT / "docs" / "FROZEN_IMPLEMENTATION_SPEC.md"),
        "started_utc": datetime.now(UTC).isoformat(),
    }

    command = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--userdir", str(USER_DATA),
        "--strategy-path", str(STRATEGY_DIR),
        "-c", str(CONFIG),
        "--strategy", STRATEGY,
        "--timerange", TIMERANGE,
        "--cache", "none",
        "--export", "trades",
        "--fee", repr(FEE),
    ]
    log = RUNS / f"p3_exp004a_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.log"
    print("P3-EXP-004A AUTHORIZED — executing exactly one preregistered run.")
    cp = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, check=False)
    log.write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + cp.stdout +
        "\nSTDERR\n" + cp.stderr, encoding="utf-8"
    )
    if cp.returncode != 0:
        raise RuntimeError(f"Freqtrade backtest failed; see {log}")

    export = find_export()
    result = read_export(export)

    after_gate = load_gate()
    after = {
        "gate": after_gate,
        "strategy_sha256": sha256(STRATEGY_FILE),
        "config_sha256": sha256(CONFIG),
        "frozen_spec_sha256": sha256(ROOT / "docs" / "FROZEN_IMPLEMENTATION_SPEC.md"),
        "completed_utc": datetime.now(UTC).isoformat(),
    }

    report = {
        "experiment_id": "P3-EXP-004A",
        "status": "EXECUTED",
        "diagnostic_only": False,
        "live_trading": False,
        "promotion": False,
        "timerange": TIMERANGE,
        "fee_per_side": FEE,
        "strategy": STRATEGY,
        "config": str(CONFIG.relative_to(ROOT)),
        "strategy_path": str(STRATEGY_FILE.relative_to(ROOT)),
        "data_directory": str(DATA.relative_to(ROOT)),
        "data_files": [str(p.relative_to(ROOT)) for p in data_files],
        "command": command,
        "log": str(log.relative_to(ROOT)),
        "export": str(export.relative_to(ROOT)),
        "integrity_before": before,
        "integrity_after": after,
        "result": result,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    raw = RUNS / f"P3-EXP-004A_RAW_{stamp}.json"
    raw.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Never promote automatically. The result is evidence only.
    print(f"RAW RESULT: {raw}")
    print("P3-EXP-004A EXECUTION FINISHED.")
    print("Promotion remains FALSE.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
