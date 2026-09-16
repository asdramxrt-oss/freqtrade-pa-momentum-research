"""P3-EXP-003 runner: perpetual funding carry (standalone).

Runs the single-leg funding-harvest research strategy over the preregistered
windows against the genuine futures dataset, and additionally reports the total
funding PnL the engine applied (proof that funding is modelled, not assumed).

Usage::

    python user_data/scripts/p3_exp003_carry.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "user_data" / "scripts"))

from exp003_backtest import analyse  # noqa: E402

USER_DATA = PROJECT_ROOT / "user_data"
DATA_P3 = USER_DATA / "data_p3"
STRATEGY_PATH = PROJECT_ROOT / "research_lib" / "strategies"
CONFIG = USER_DATA / "configs" / "P3-EXP-003.json"
RESULTS_DIR = USER_DATA / "backtest_results"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "P3-EXP-003.raw.json"
LOG_DIR = Path(os.environ.get("TEMP", ".")) / "pa-momentum-research"

STRATEGY = "FundingCarry"
WINDOWS = {
    "full": "20190908-20260916",
    "train": "20190908-20221231",
    "validation": "20230101-20241231",
    "test": "20250101-20260916",
}
FEE = 0.0005


def run_window(timerange: str, label: str) -> dict:
    """
    Run one carry backtest and return the parsed result.

    :param timerange: freqtrade timerange.
    :param label: Log label.
    :return: Parsed result.
    :raises RuntimeError: On a non-zero exit.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "freqtrade",
        "backtesting",
        "--userdir",
        str(USER_DATA),
        "-d",
        str(DATA_P3),
        "--strategy-path",
        str(STRATEGY_PATH),
        "-c",
        str(CONFIG),
        "--strategy",
        STRATEGY,
        "--timerange",
        timerange,
        "--cache",
        "none",
        "--export",
        "trades",
        "--fee",
        repr(FEE),
    ]
    completed = subprocess.run(
        command, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=os.environ.copy()
    )
    log_file = LOG_DIR / f"{label}.log"
    log_file.write_text(
        "$ " + " ".join(command) + "\n\n" + completed.stdout + "\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"backtest failed for {label}; see {log_file}")

    pointer = json.loads((RESULTS_DIR / ".last_result.json").read_text(encoding="utf-8"))
    export = RESULTS_DIR / pointer["latest_backtest"]
    if export.suffix == ".zip":
        with zipfile.ZipFile(export) as archive:
            member = next(
                name
                for name in archive.namelist()
                if name.endswith(".json") and not name.endswith("_config.json")
            )
            result = json.loads(archive.read(member))
    else:
        result = json.loads(export.read_text(encoding="utf-8"))
    result["_command"] = " ".join(command)
    return result


def main() -> int:
    """
    Run the carry experiment over all windows and write the raw result.

    :return: Process exit code.
    """
    output: dict = {
        "experiment_id": "P3-EXP-003",
        "dataset": str(DATA_P3.relative_to(PROJECT_ROOT)),
        "config": str(CONFIG.relative_to(PROJECT_ROOT)),
        "strategy": STRATEGY,
        "generated_utc": datetime.now(UTC).isoformat(),
        "runs": {},
    }
    if OUTPUT.exists():
        output["runs"] = json.loads(OUTPUT.read_text(encoding="utf-8")).get("runs", {})

    for window, timerange in WINDOWS.items():
        print(f"  carry {window:11} {timerange} ...", flush=True)
        result = run_window(timerange, f"p3-exp003-{window}")
        strategy_name = next(iter(result["strategy"]))
        trades = result["strategy"][strategy_name]["trades"]
        funding_pnl = float(sum(t.get("funding_fees", 0.0) or 0.0 for t in trades))
        metrics = analyse(result)
        output["runs"][window] = {
            "timerange": timerange,
            "command": result.pop("_command"),
            "funding_fees_applied_usdt": funding_pnl,
            "trades": len(trades),
            "metrics": metrics,
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(
            f"      trades={metrics['trades']} PF={metrics['profit_factor']:.4f} "
            f"net={metrics['net_profit_pct']:.2f}% ddW={metrics['max_drawdown_wallet_pct']:.2f}% "
            f"p={metrics['p_value']:.4f} funding_applied={funding_pnl:,.0f} USDT",
            flush=True,
        )

    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
