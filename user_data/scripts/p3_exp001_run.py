"""P3-EXP-001 runner: genuine-futures Turtle, long/short x signal/sizing arms.

Runs the four preregistered arms over the preregistered windows against the
GENUINE futures dataset in a separate datadir, and records metrics.

It contains no strategy logic and selects no parameter. Research code only; the
production strategy and the historical spot mirror are untouched.

Usage::

    python user_data/scripts/p3_exp001_run.py
    python user_data/scripts/p3_exp001_run.py --window full
    python user_data/scripts/p3_exp001_run.py --arm long_vol
"""

from __future__ import annotations

import argparse
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
CONFIG = USER_DATA / "configs" / "P3-EXP-001.json"
RESULTS_DIR = USER_DATA / "backtest_results"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "P3-EXP-001.raw.json"
LOG_DIR = Path(os.environ.get("TEMP", ".")) / "pa-momentum-research"

ARMS = {
    "long_vol": "TurtleFuturesLong",
    "long_raw": "TurtleFuturesLongRaw",
    "short_vol": "TurtleFuturesShort",
    "short_raw": "TurtleFuturesShortRaw",
}
WINDOWS = {
    "full": "20190908-20260916",
    "train": "20190908-20221231",
    "validation": "20230101-20241231",
    "test": "20250101-20260916",
}
FEE = 0.0005


def run_arm(arm: str, strategy: str, window: str, timerange: str) -> dict:
    """
    Execute one arm/window backtest and return the raw result.

    :param arm: Arm key.
    :param strategy: Strategy class name.
    :param window: Window key.
    :param timerange: freqtrade timerange.
    :return: Parsed backtest result.
    :raises RuntimeError: On a non-zero freqtrade exit.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    label = f"p3-exp001-{arm}-{window}"
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
        strategy,
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
    Run the requested P3-EXP-001 arms/windows and write the raw result file.

    :return: Process exit code.
    """
    parser = argparse.ArgumentParser(description="P3-EXP-001 runner")
    parser.add_argument("--arm", choices=list(ARMS), default="")
    parser.add_argument("--window", choices=list(WINDOWS), default="")
    args = parser.parse_args()

    arms = [args.arm] if args.arm else list(ARMS)
    windows = [args.window] if args.window else list(WINDOWS)

    output: dict = {
        "experiment_id": "P3-EXP-001",
        "dataset": str(DATA_P3.relative_to(PROJECT_ROOT)),
        "config": str(CONFIG.relative_to(PROJECT_ROOT)),
        "strategy_path": str(STRATEGY_PATH.relative_to(PROJECT_ROOT)),
        "generated_utc": datetime.now(UTC).isoformat(),
        "runs": {},
    }
    if OUTPUT.exists():
        output["runs"] = json.loads(OUTPUT.read_text(encoding="utf-8")).get("runs", {})

    print(
        f"P3-EXP-001: {len(arms)} arms x {len(windows)} windows = {len(arms) * len(windows)} runs"
    )
    for arm in arms:
        output["runs"].setdefault(arm, {})
        for window in windows:
            timerange = WINDOWS[window]
            print(f"  {arm:10} {window:11} {timerange} ...", flush=True)
            result = run_arm(arm, ARMS[arm], window, timerange)
            metrics = analyse(result)
            output["runs"][arm][window] = {
                "timerange": timerange,
                "strategy": ARMS[arm],
                "command": result.pop("_command"),
                "metrics": metrics,
            }
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
            print(
                f"      trades={metrics['trades']} PF={metrics['profit_factor']:.4f} "
                f"net={metrics['net_profit_pct']:.2f}% ddW={metrics['max_drawdown_wallet_pct']:.2f}% "
                f"p={metrics['p_value']:.4f}",
                flush=True,
            )

    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
