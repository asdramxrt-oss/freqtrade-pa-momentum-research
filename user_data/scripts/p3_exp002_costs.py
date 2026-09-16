"""P3-EXP-002 runner: Turtle long cost / slippage sensitivity.

Preregistered grid: fee per side in {0.05%, 0.10%, 0.20%} x slippage per side in
{0.00%, 0.05%, 0.15%}. freqtrade models slippage only through the fee parameter,
so each cell's *effective* per-side cost is ``fee + slippage``. Several cells
collapse to the same effective cost, so each unique effective cost is run once
and the mapping is recorded (no cherry-picking, no post-hoc scenario choice).

Applies to the P3-EXP-001 long arms (the only direction with any positive
in-sample result). No parameter is changed; the signal, stops, sizing and exits
are exactly P3-EXP-001's.

Usage::

    python user_data/scripts/p3_exp002_costs.py
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
CONFIG = USER_DATA / "configs" / "P3-EXP-001.json"
RESULTS_DIR = USER_DATA / "backtest_results"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "P3-EXP-002.raw.json"
LOG_DIR = Path(os.environ.get("TEMP", ".")) / "pa-momentum-research"

# Preregistered grid (per side).
FEE_LEVELS = [0.0005, 0.0010, 0.0020]  # 0.05%, 0.10%, 0.20%
SLIP_LEVELS = [0.0, 0.0005, 0.0015]  # 0.00%, 0.05%, 0.15%

ARMS = {"long_vol": "TurtleFuturesLong", "long_raw": "TurtleFuturesLongRaw"}
FULL = "20190908-20260916"
TEST = "20250101-20260916"
STRESS_FEE = 0.0035


def grid_cells() -> dict[float, list[str]]:
    """
    Map each unique effective cost to the grid cells that produce it.

    :return: ``{effective_fee: ["0.05%+0.15%", ...]}``.
    """
    cells: dict[float, list[str]] = {}
    for fee in FEE_LEVELS:
        for slip in SLIP_LEVELS:
            effective = round(fee + slip, 6)
            cells.setdefault(effective, []).append(f"fee{fee * 100:.2f}%+slip{slip * 100:.2f}%")
    return dict(sorted(cells.items()))


def run_backtest(strategy: str, timerange: str, fee: float, label: str) -> dict:
    """
    Run one backtest and return the parsed result.

    :param strategy: Research strategy class name.
    :param timerange: freqtrade timerange.
    :param fee: Effective per-side cost.
    :param label: Log label.
    :return: Parsed result.
    :raises RuntimeError: On non-zero exit.
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
        strategy,
        "--timerange",
        timerange,
        "--cache",
        "none",
        "--export",
        "trades",
        "--fee",
        repr(fee),
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
    Run the preregistered cost grid and write the raw result.

    :return: Process exit code.
    """
    cells = grid_cells()
    output: dict = {
        "experiment_id": "P3-EXP-002",
        "dataset": str(DATA_P3.relative_to(PROJECT_ROOT)),
        "generated_utc": datetime.now(UTC).isoformat(),
        "preregistered_grid": {
            "fee_levels": FEE_LEVELS,
            "slippage_levels": SLIP_LEVELS,
            "unique_effective_fees": {str(k): v for k, v in cells.items()},
            "note": "freqtrade models slippage through the fee parameter; effective cost = fee + slippage",
        },
        "runs": {},
    }
    if OUTPUT.exists():
        output["runs"] = json.loads(OUTPUT.read_text(encoding="utf-8")).get("runs", {})

    print(f"P3-EXP-002 unique effective fees: {list(cells)}")
    for arm, strategy in ARMS.items():
        output["runs"].setdefault(arm, {})
        for effective in list(cells):
            label = f"p3-exp002-{arm}-full-{effective:.4f}"
            print(f"  {arm:9} full eff={effective:.4f} ...", flush=True)
            result = run_backtest(strategy, FULL, effective, label)
            metrics = analyse(result)
            output["runs"][arm][f"full_{effective:.4f}"] = {
                "effective_fee_per_side": effective,
                "grid_cells": cells[effective],
                "timerange": FULL,
                "command": result.pop("_command"),
                "metrics": metrics,
            }
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
            print(
                f"      PF={metrics['profit_factor']:.4f} net={metrics['net_profit_pct']:.1f}% "
                f"ddW={metrics['max_drawdown_wallet_pct']:.1f}% fees={metrics['fees_paid_usdt']:,.0f}",
                flush=True,
            )

        label = f"p3-exp002-{arm}-test-stress"
        print(f"  {arm:9} test  eff={STRESS_FEE:.4f} (stress) ...", flush=True)
        result = run_backtest(strategy, TEST, STRESS_FEE, label)
        metrics = analyse(result)
        output["runs"][arm]["test_0.0035"] = {
            "effective_fee_per_side": STRESS_FEE,
            "grid_cells": ["fee0.20%+slip0.15%"],
            "timerange": TEST,
            "command": result.pop("_command"),
            "metrics": metrics,
        }
        OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(
            f"      PF={metrics['profit_factor']:.4f} net={metrics['net_profit_pct']:.1f}% "
            f"ddW={metrics['max_drawdown_wallet_pct']:.1f}%",
            flush=True,
        )

    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
