# Walk-forward validation

Walk-forward testing is **not** applied to strategies that have already failed
the preliminary charter criteria. Running walk-forward on EXP-001 as it stands
would produce a lot of machinery built on a setup whose per-trade expectancy is
not even significant.

A strategy enters this directory only after it passes charter criteria A1–A8.

## What belongs here

| Artifact | Purpose |
|----------|---------|
| `walk_forward_config.json` | Window definition: in-sample length, out-of-sample length, step |
| `run_walk_forward.py` | Harness that runs freqtrade per window and stitches results |
| `<EXPERIMENT_ID>_walk_forward.md` | Per-window results and the stability verdict |

## Definition of the window scheme (to be fixed before first use)

Planned anchored walk-forward for a daily/4h trend system:

- in-sample (design) window: 3 years
- out-of-sample (evaluation) window: 1 year
- step: 1 year

Parameters are chosen on the in-sample window only. The out-of-sample year is
evaluated once. No window may overlap the 2025 holdout reserved by the frozen
protocol without a new experiment ID.

## What walk-forward must report

1. Per-window return, profit factor, trade count and drawdown.
2. Whether the out-of-sample windows are consistently positive or whether the
   headline result depends on one or two windows.
3. Parameter drift across windows. Large drift is evidence the setup has no
   stable optimum and that any in-sample choice is arbitrary.
4. The ratio of out-of-sample to in-sample performance. A large, systematic decay
   is the expected signature of overfitting and must be reported plainly.
