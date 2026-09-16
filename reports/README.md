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
