# Research scripts

Two scripts, both deliberately thin wrappers over `freqtrade` so that an
experiment is reproducible from its ID and its documented timerange.

| Script | Purpose |
|--------|---------|
| `download_data.ps1` | Fetch the pre-registered market data (git-ignored, reproducible) |
| `run_experiment.ps1` | Run a pre-registered backtest and print the charter-required metrics |

## Prerequisites

`freqtrade` must be importable by the `python` on `PATH`. Freqtrade is supplied
as a source checkout rather than a pinned PyPI dependency, so that the exact
framework revision used for a run is explicit:

```powershell
$env:FREQTRADE_SRC = "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop"
```

Both scripts copy `FREQTRADE_SRC` into `PYTHONPATH` when `PYTHONPATH` is unset.

## Usage

```powershell
# pre-registered data universe
./user_data/scripts/download_data.ps1

# full-sample baseline
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001

# cost sensitivity
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001 -Fee 0.002

# out-of-sample holdout (one evaluation per strategy version)
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001 -Timerange 20250101-20260101
```

## Rules these scripts exist to enforce

1. **One config per experiment.** `run_experiment.ps1` refuses to run if
   `user_data/configs/<Experiment>.json` does not exist, so nothing is executed
   without a committed configuration.
2. **Logs are written outside the repository** (to `%TEMP%`), so raw backtest
   output cannot accidentally be committed. Only summarised, reviewed results
   are written into `research/experiment_results/`.
3. **No parameter selection in the runner.** The scripts pass timerange and fee
   only. Anything else that changes a result must live in the committed config,
   where it is reviewable.
