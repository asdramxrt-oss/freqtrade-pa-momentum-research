# Research Charter — PA Momentum Research

**Status:** FROZEN
**Frozen on:** 2026-09-16
**Frozen at commit:** see `research/decisions/DECISION_LOG.md` (DEC-001)
**Applies to:** every experiment in `freqtrade-pa-momentum-research`

This charter governs how research is conducted in this repository. It exists so
that a conclusion can be trusted *because of the process that produced it*, not
because the backtest number happened to look good.

Changing anything in this document requires a new decision record in
`research/decisions/DECISION_LOG.md` explaining why the rule was wrong.

---

## 1. Isolation rules

1. **Production code is never modified by this research project.** Live trading
   systems, validated research repositories and exchange configuration that
   exist elsewhere on this machine are read-only to this project. This project
   owns exactly one directory and one repository.
2. **No live trading is ever enabled from research code.** All strategies in
   this repository are backtest / dry-run / research only. Promotion to live is
   a separate, explicit production-readiness stage (§13).
3. **Secrets never enter the repository.** API keys, secrets and credentials
   live in environment variables or git-ignored local config only.

## 2. Methodology rules

4. **Every strategy begins as a standalone rule-based baseline.** No ML, no
   regime classifier, no portfolio router in a baseline.
5. **Turtle/Donchian is the reference baseline.** Every other strategy must be
   comparable to it under identical conditions.
6. **No ML is added to a strategy until its rule-based version has been
   independently tested and its results recorded.**
7. **No portfolio router is created before the component strategies have been
   independently evaluated.** A router must never be used to rescue a weak
   strategy.
8. **Same market universe and cost assumptions for comparable experiments.**
   Deviations must be recorded in the experiment specification *before* the run
   and must be reported alongside the result.
9. **No future information may enter features, labels, signals or execution
   logic.** All calculations must be causal. Any signal intended to be actable
   at bar `t` may only consume data from bars `<= t`.
10. **Hyperparameters must be recorded** for every run, including defaults.
11. **Dataset dates must be recorded** for every run, per pair.
12. **Train / validation / test / walk-forward boundaries must be recorded**
    before a run, not chosen after seeing the result.

## 3. Evidence rules

13. **Experiment changes must be version-controlled.** A result is only
    meaningful together with the commit SHA that produced it.
14. **Negative results are preserved.** Experiments that failed are never
    deleted, hidden or silently re-run until they look better.
15. **Do not optimise on the final untouched out-of-sample set.** The holdout is
    evaluated once per strategy version, and the number of evaluations is
    recorded.
16. **Backtest improvements must survive realistic fees and slippage.** Any
    claimed edge must be re-tested under increased cost assumptions.
17. **A strategy is not promoted because of one strong pair, year or market
    regime.** Promotion requires behaviour to hold across pairs, years and
    regimes.
18. **Statistical significance is not optional.** Per-trade expectancy must be
    tested; a positive mean with a large p-value is not evidence of an edge.

## 4. Reporting rules

19. **Never claim a pass that has not been measured.** Experiment statuses are
    factual: `PLANNED`, `RUNNING`, `COMPLETED`, `PASS`, `FAIL`, `REJECTED`,
    `FROZEN`, `PRODUCTION_CANDIDATE`.
20. **Every experiment records:** ID, hypothesis, branch, commit, dataset,
    configuration, metrics, OOS metrics, robustness results, limitations and a
    decision.
21. **Combining strategies is not assumed to help.** Complementarity must be
    demonstrated (signal overlap, return correlation, drawdown correlation,
    exposure overlap), not inferred from a higher combined profit.
22. **A failed hypothesis is a valid, reportable result.** Proceed to the next
    experiment only when the previous hypothesis has been evaluated and the
    decision recorded.

## 5. Agent behaviour rules

23. **Do not continuously optimise until a good backtest appears.** For every
    implementation: read the spec, inspect existing code, implement the smallest
    clean version, write tests, run tests, run the baseline experiment, save
    reproducible results, record findings, update Git, stop and evaluate.
24. **When results are poor: investigate and document, do not hide and do not
    arbitrarily add indicators.**
25. **When results are good: attempt to falsify them** — test costs, OOS,
    robustness, parameter sensitivity.

---

## Pre-registered experiment sequence

| ID | Experiment | Depends on |
|----|-----------|-----------|
| EXP-001 | Turtle raw baseline | — |
| EXP-002 | Turtle with realistic transaction costs | EXP-001 |
| EXP-003 | Pullback continuation standalone | EXP-002 |
| EXP-004 | Turtle + Pullback | EXP-003 |
| EXP-005 | Breakout-retest standalone | EXP-004 |
| EXP-006 | Turtle + Breakout-retest | EXP-005 |
| EXP-007 | Volatility expansion standalone | EXP-006 |
| EXP-008 | Turtle + Volatility expansion | EXP-007 |
| EXP-009 | Swing-structure standalone | EXP-008 |
| EXP-010 | ML on Turtle | EXP-002 |
| EXP-011 | ML on Pullback | EXP-010 |
| EXP-012 | ML on Breakout-retest | EXP-011 |
| EXP-013 | ML on Volatility expansion | EXP-012 |
| EXP-014 | Cross-strategy interaction analysis | EXP-013 |
| EXP-015 | Portfolio / router research | EXP-014 |

Residual/cross-sectional momentum and carry/basis research stay conceptually
separate from pure price-action strategies and are not added merely because
they sound complementary.

## Acceptance thresholds

A strategy "survives preliminary evaluation" only if **all** of the following
hold, measured with the pre-registered protocol in
`research/preregistration/experiment_protocol.md`:

| # | Criterion | Threshold |
|---|-----------|-----------|
| A1 | Trades (sample sufficiency) | >= 200 |
| A2 | Profit factor, full period, fee 0.05% | >= 1.10 |
| A3 | Per-trade expectancy p-value | < 0.05 |
| A4 | OOS net return | >= 0 |
| A5 | OOS profit factor | >= 1.00 |
| A6 | Max drawdown, wallet balance | < 35% |
| A7 | Profitable calendar years | >= 60% |
| A8 | Profit factor at fee 0.20% | >= 1.05 |

Failing any criterion is recorded as a `FAIL` with the specific criterion
named. Failing A2–A8 does not necessarily mean the idea is worthless — it means
the idea is not yet evidence of an edge and cannot be promoted or combined.
