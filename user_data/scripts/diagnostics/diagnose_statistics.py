"""PHASE 2 diagnostic: statistical tests on frozen-strategy trade returns.

A small, pre-specified set of tests (bootstrap CIs and permutation tests) to avoid
multiple-comparison inflation. Reads the trade lists recorded by
``diagnose_trades.py``; it does not re-run or alter any strategy.

Usage::

    python user_data/scripts/diagnostics/diagnose_statistics.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diag_common import PROJECT_ROOT, bootstrap_ci, permutation_test, write_json  # noqa: E402

INPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_trade_diagnostics.json"
OUTPUT = PROJECT_ROOT / "research" / "experiment_results" / "PHASE2_statistics.json"

PERIODS = ["D_development", "C_consumed_2025", "F_fresh_2026"]


def main() -> int:
    """
    Run the pre-specified statistical tests and write the result.

    :return: Process exit code.
    """
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    output = {
        "phase": "PHASE2",
        "generated_utc": datetime.now(UTC).isoformat(),
        "notes": [
            "Two-sided one-sample bootstrap of the mean per-trade profit (USDT).",
            "Two-sided permutation test of a difference in means between periods.",
            "Small pre-specified test set to limit multiple-comparison inflation.",
            "Trade profits are in absolute USDT, so compounding-era development "
            "trades are large; the comparison is directional, not scale-free.",
        ],
        "strategies": {},
    }

    for strategy, periods in data["strategies"].items():
        output["strategies"][strategy] = {"ci": {}, "permutation": {}}
        for period in PERIODS:
            profits = periods[period]["trade_profits_usdt"]
            output["strategies"][strategy]["ci"][period] = {
                "n": len(profits),
                **bootstrap_ci(profits),
            }
        for left, right in (("D_development", "F_fresh_2026"), ("C_consumed_2025", "F_fresh_2026")):
            output["strategies"][strategy]["permutation"][f"{left}_vs_{right}"] = permutation_test(
                periods[left]["trade_profits_usdt"], periods[right]["trade_profits_usdt"]
            )

    write_json(OUTPUT, output)

    for strategy, blocks in output["strategies"].items():
        print(f"===== {strategy}")
        for period, ci in blocks["ci"].items():
            print(
                f"  {period:20} n={ci['n']:4} mean={ci['point']:>9.2f} "
                f"95% CI [{ci['low']:>9.2f}, {ci['high']:>9.2f}]"
            )
        for key, test in blocks["permutation"].items():
            print(
                f"  {key:34} diff={test['observed_diff']:>9.2f} p={test['p_value']:.4f} "
                f"(n={test['n_a']}/{test['n_b']})"
            )
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
