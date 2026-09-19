# Walk-forward validation

Walk-forward testing is **not** applied to strategies that have already failed
the preliminary charter criteria. Running walk-forward on EXP-001 as it stands
would produce a lot of machinery built on a setup whose per-trade expectancy is
not even significant.

> **Original entry rule (still in force for confirmatory use):**
> "A strategy enters this directory only after it passes charter criteria A1–A8."

**Reconciliation for diagnostic-only use (DEC-007, 2026-09-16).** The rule above
continues to govern any *confirmatory* walk-forward and any strategy considered
for promotion. It is reconciled — **by record, not by editing the frozen
specification** — with `docs/FROZEN_IMPLEMENTATION_SPEC.md` §9 for
**diagnostic-only** use: the already-implemented, already-failed engines
(P3-EXP-001 long arms and P3-EXP-003 carry) may be walked forward strictly to
measure **stability, decay and reproducibility across windows**. This is not
validation, not promotion and not a strategy verdict. Any window overlapping
2025–2026 is labelled **NON-PRISTINE**. See `research/decisions/DECISION_LOG.md`
DEC-007 and `research/walk_forward/walk_forward_config.json`.

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
