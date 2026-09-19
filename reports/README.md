# Reports

Generated, human-readable artifacts derived from recorded experiment results.

## Rules

1. **Nothing here is a source of truth.** The source of truth is
   `research/experiment_results/`. A report is a view over those files, and if a
   report disagrees with a result document, the result document wins.
2. **Reports are reproducible from committed inputs.** A report must be
   regenerable from the result JSON artifacts without re-running a backtest.
   That way a chart cannot silently diverge from the recorded numbers.
3. **No report may be used to declare a pass.** Acceptance is decided only by the
   charter criteria evaluated against the recorded metrics.
4. **Raw backtest logs do not live here.** The runner writes logs to `%TEMP%`, so
   unreviewed engine output cannot be mistaken for a result.

## Planned reports

| Report | Input | Purpose |
|--------|-------|---------|
| `EXP-001_summary.md` | `research/experiment_results/EXP-001.json` | One-page baseline summary |
| `cost_sensitivity.md` | all result JSONs | Fee/slippage sweep across strategies |
| `complementarity.md` | paired strategy results | Signal overlap, return and drawdown correlation |
| `year_matrix.md` | all result JSONs | Strategy x year robustness grid |

## Generated bridge report

`reports/<run_id>_REPORT.md` is produced by `automation/report.py` via the
one-click bridge (`run_bridge.ps1` / `python -m automation.bridge`). It obeys the
rules above: it is a derived view over the recorded JSON, it is regenerable
without re-running a backtest, and it contains no wall-clock timestamps, so
identical inputs produce byte-identical output. It is never a source of truth
and cannot declare a pass. The companion next-task file
`.mece/NEXT_TASK.md` is a proposal only.
