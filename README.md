# freqtrade-pa-momentum-research

Evidence-based research into **price-action momentum strategies** for crypto
markets, built on [Freqtrade](https://www.freqtrade.io/).

This repository exists to answer one question honestly:

> Do price-action momentum setups provide a genuine, robust, cost-surviving edge
> — and are different setups actually *different*, or just the same trades wearing
> a different name?

The objective is **not** to maximise a backtest number. It is to produce
reproducible experiments whose conclusions survive contact with costs,
out-of-sample data, other pairs, other years and other regimes.

---

## Headline status of the programme

| Experiment | Strategy | Status | Result |
|-----------|----------|--------|--------|
| EXP-001 | Turtle / Donchian raw baseline | **FAIL** | 4/8 charter criteria. p=0.066, OOS −18.98%, max DD 61.6% |
| EXP-002 | Turtle with realistic transaction costs | PLANNED | — |
| EXP-003 | Pullback continuation standalone | PLANNED | — |
| EXP-004 | Turtle + Pullback | PLANNED | — |
| EXP-005 | Breakout-retest standalone | PLANNED | — |
| EXP-006 | Turtle + Breakout-retest | PLANNED | — |
| EXP-007 | Volatility expansion standalone | PLANNED | — |
| EXP-008 | Turtle + Volatility expansion | PLANNED | — |
| EXP-009 | Swing-structure standalone | PLANNED | — |
| EXP-010–013 | ML second-stage filters (one per setup) | PLANNED | — |
| EXP-014 | Cross-strategy interaction analysis | PLANNED | — |
| EXP-015 | Portfolio / router research | PLANNED | — |

The baseline failing is a **valid and useful result**. It is recorded, not
hidden, and it is not going to be "fixed" by tuning.

---

## Research philosophy

1. **The reference baseline is sacred.** Turtle/Donchian is the yardstick. It is
   never tuned to look better, because a tuned baseline makes every later
   comparison meaningless.
2. **Standalone first, combined later.** Every setup is tested on its own before
   it is allowed anywhere near another strategy.
3. **Rule-based before ML.** ML is a *second-stage filter over an existing valid
   setup*, never a free-standing trade generator.
4. **No router to rescue weak ideas.** A portfolio layer only ever chooses among
   already-validated setups.
5. **Causality is a hard requirement.** A decision at bar `t` may only use bars
   `<= t`. Look-ahead is treated as a correctness bug, and there is a test for it.
6. **Negative results are first-class.** Failed experiments stay in the
   repository with their numbers attached.
7. **Costs are part of the hypothesis.** An edge that dies at 0.10% per side is
   not an edge.
8. **Complementarity is demonstrated, not assumed.** Combining strategies must
   show different trades and different return streams, not just a bigger total.
9. **Nothing here can trade live.** Research code is backtest / dry-run only.

Governance: `research/preregistration/research_charter.md` (frozen).
Evaluation protocol: `research/preregistration/experiment_protocol.md` (frozen).

---

## Architecture

Signals, risk and execution are separated so each can be tested in isolation.

```
candles
   |
   v
[ indicators ]     user_data/strategies/shared/pa_indicators.py   pure, causal, no freqtrade
   |
   v
[ signals ]        user_data/strategies/shared/pa_signals.py      pure, causal, no freqtrade
   |
   v
[ strategy ]       user_data/strategies/<family>/<Name>.py        freqtrade IStrategy
   |
   v
[ risk ]           user_data/strategies/shared/pa_risk.py         pure sizing / stop maths
   |
   v
freqtrade engine (backtest only)
```

The ML path, when it is eventually introduced, sits *inside* this flow as a
second-stage scorer over setups that already satisfy the rule-based definition:

```
PRICE -> RULE-BASED SETUP -> FEATURE ENGINE -> SPECIALISED MODEL -> SCORE -> RISK -> EXECUTION
```

Never `PRICE -> MODEL -> TRADE`.

`pa_indicators`, `pa_signals` and `pa_risk` deliberately do **not** import
`freqtrade`, so the logic that determines trades can be unit-tested in
milliseconds with no framework, no data download and no exchange.

---

## Directory structure

```
freqtrade-pa-momentum-research/
|-- README.md
|-- .gitignore
|-- pyproject.toml
|-- conftest.py                     pytest bootstrap (paths + freqtrade discovery)
|
|-- research/                       the research record (source of truth for "why")
|   |-- preregistration/
|   |   |-- research_charter.md      frozen governance rules
|   |   `-- experiment_protocol.md   frozen universe / periods / costs / thresholds
|   |-- hypotheses/                  one document per strategy idea
|   |-- experiment_specs/            fixed BEFORE a run
|   |-- experiment_results/          recorded AFTER a run (md + machine-readable json)
|   |-- walk_forward/                walk-forward harness and reports
|   `-- decisions/DECISION_LOG.md    every direction-changing decision
|
|-- user_data/
|   |-- strategies/
|   |   |-- shared/                  pa_indicators, pa_signals, pa_risk
|   |   |-- turtle/                  DonchianTurtleBaseline.py  (EXP-001)
|   |   |-- pullback/                (EXP-003)
|   |   |-- breakout_retest/         (EXP-005)
|   |   `-- volatility_expansion/    (EXP-007)
|   |-- configs/                     one frozen config per experiment
|   |-- scripts/                     download_data.ps1, run_experiment.ps1
|   `-- data/                        git-ignored raw candles
|
|-- ml/                              per-strategy prediction problems (EXP-010+)
|   |-- turtle/ pullback/ breakout_retest/ volatility_expansion/
|   `-- features/ labels/ validation/
|
|-- tests/
|   |-- unit/                        indicators, signals, risk, strategy spec
|   |-- integration/                 end-to-end checks
|   `-- research/                    tests over recorded experiment artifacts
|
`-- reports/                         generated human-readable reports
```

---

## Setup

Requirements: Python 3.11+, a Freqtrade source checkout, PowerShell on Windows
(the scripts are PowerShell; the underlying commands are cross-platform).

Freqtrade is intentionally **not** pinned in `pyproject.toml`. It is supplied as
an explicit checkout so that the framework revision behind a result is a recorded
fact rather than a moving PyPI release:

```powershell
$env:FREQTRADE_SRC = "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop"
```

Nothing is written into the freqtrade checkout. `PYTHONPATH` is used instead of
an editable install, so the host environment and the framework source stay
untouched.

---

## Running the tests

```powershell
$env:PYTHONPATH = "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop"
python -m pytest tests -q
```

`conftest.py` resolves freqtrade from `FREQTRADE_SRC`, or from a
`../freqtrade-develop/freqtrade-develop` sibling directory, or skips the
freqtrade-dependent tests if neither is available.

Current status: **76 tests passing.**

What the tests pin down:

- Donchian channels **exclude the current bar**, and are prefix-invariant
  (the causal/look-ahead test).
- ATR matches a hand-computed Wilder recursion seeded like TA-Lib.
- Breakouts do not fire on a high without a closing breakout.
- Exactly one entry per breakout episode (duplicate-signal suppression).
- `rising_edge` never fires on bar 0.
- Position sizing risks the requested fraction and respects caps.
- The strategy's fixed parameters, long-only behaviour and disabled ROI.
- Strategy signals are prefix-invariant end-to-end.

---

## Running an experiment

```powershell
# 1. fetch the pre-registered data (git-ignored, reproducible)
./user_data/scripts/download_data.ps1

# 2. full-sample run, base cost
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001

# 3. cost sensitivity
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001 -Fee 0.002

# 4. out-of-sample holdout (ONE evaluation per strategy version)
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001 -Timerange 20250101-20260101
```

Or directly:

```powershell
python -m freqtrade backtesting --userdir user_data -c user_data/configs/EXP-001.json `
    --timerange 20190101-20260101 --cache none
```

List the strategies freqtrade can see:

```powershell
python -m freqtrade list-strategies --userdir user_data -c user_data/configs/EXP-001.json
```

---

## Experiment lifecycle

1. **Hypothesis** — write `research/hypotheses/<topic>.md`.
2. **Specification** — write `research/experiment_specs/EXP-0NN.md` and
   `user_data/configs/EXP-0NN.json`. **Commit before running.**
3. **Implementation** — smallest clean version, signals separated from risk.
4. **Tests** — write them, run them, make them pass.
5. **Run** — base cost, per-year, OOS once, cost stress.
6. **Record** — `research/experiment_results/EXP-0NN.md` plus `EXP-0NN.json`.
7. **Evaluate** — charter criteria A1–A8, criterion by criterion.
8. **Decide** — `research/decisions/DECISION_LOG.md`.
9. **Update Git** — commit on the experiment branch.
10. **Update Notion** — create/update the experiment record with branch, commit
    SHA, dataset, config, metrics, OOS, robustness, limitations, decision.
11. **Stop and evaluate before adding complexity.**

An experiment whose hypothesis fails is finished, not failed. The next
experiment only begins when the current one has a recorded decision.

---

## Git workflow

```
main
 |-- research/turtle-baseline      EXP-001  (created)
 |-- research/pullback             EXP-003/004
 |-- research/breakout-retest      EXP-005/006
 |-- research/volatility-expansion EXP-007/008
 |-- research/swing-structure      EXP-009
 |-- research/ml-validation        EXP-010..013
 `-- research/portfolio-router     EXP-014/015
```

- `main` holds the shared foundation: charter, protocol, tooling, tests, the
  baseline, and the research record.
- Each substantial experiment gets its own `research/*` branch.
- **A higher backtest number is not a reason to merge.** Merging requires the
  decision record to justify it.
- Commit messages reference the experiment ID, so a result maps to a commit.
- Experiment branches are merged only as a *record* (specs, results, decisions),
  which is what makes `main` the institutional memory of the programme.

---

## Notion workflow

Notion is the **research control plane** — not a code store. Code, tests and
configs live only in Git.

Hierarchy:

```
AI Trading Research
`-- Freqtrade PA Momentum Research
    |-- 00 - Project Control
    |-- 01 - Research Charter
    |-- 02 - Strategy Specifications
    |-- 03 - Experiments            <- database, one row per EXP-0NN
    |-- 04 - Results
    |-- 05 - Walk Forward
    |-- 06 - Decisions / Rejected Ideas
    |-- 07 - Production Readiness
    `-- 08 - Architecture
```

Each experiment row carries: Experiment ID, Strategy, Version, Hypothesis,
Status, GitHub branch, GitHub PR, Git commit, Dataset period, Pairs, Timeframe,
Fees, Slippage, Return, Profit Factor, Max Drawdown, Trade Count, Win Rate,
Expectancy, OOS Result, Walk-forward Result, Pair Robustness, Year Robustness,
Decision, Notes.

Statuses: `PLANNED`, `RUNNING`, `COMPLETED`, `PASS`, `FAIL`, `REJECTED`,
`FROZEN`, `PRODUCTION_CANDIDATE`.

Nothing is marked `PASS` until the charter's validation tests have actually run
and their measured values are recorded.

---

## Production isolation policy

- This project **never** modifies, deletes, refactors or overwrites any other
  trading project, production strategy, live configuration or previously
  validated research repository on this machine.
- This project owns exactly one directory and one repository.
- No live trading is enabled from this repository. All strategies are backtest /
  dry-run / research only.
- Promotion to live requires a separate, explicit production-readiness stage
  (`research/decisions/DECISION_LOG.md` and `07 - Production Readiness` in
  Notion), and is out of scope for the current milestone.
- Credentials never enter Git. See `.gitignore` and `.env.example`.

---

## Baseline result in one paragraph

The raw Turtle baseline traded 1,347 times over 2019–2026 on 10 Binance spot
pairs and returned +4,817% compounded at 0.05% fees with a 1.23 profit factor —
but its per-trade expectancy is not statistically significant (p = 0.066), its
untouched 2025 holdout lost 18.98% with a profit factor of 0.80, and its wallet
drawdown reached 61.6%. Tripling fees removed roughly 57% of the compounded
return. It fails 4 of 8 pre-registered acceptance criteria and is retained
strictly as the reference baseline. Full detail:
`research/experiment_results/EXP-001.md`.
