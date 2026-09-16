# Repository Audit — `freqtrade-pa-momentum-research`

**Phase A deliverable.** Read-only inspection of the repository, environment and
research record. No production strategy code was modified.

| Item | Value |
|------|-------|
| Audit date | 2026-09-16 |
| Branch audited | `research/diagnostic-generalization` @ `33f3702` (audit written at `8256cbc`+ ) |
| Repo root | `C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research` |
| Framework | freqtrade `2026.9-dev` (source checkout, not pinned) |

---

## A1. Git state

- Working tree clean. `main` = `536c2a4`.
- Branches: `main`, `research/turtle-baseline` (`12acbf7`),
  `research/turtle-costs` (`3481520`), `research/pullback-continuation`
  (`e6d8f88`), `research/frozen-pullback-oos` (`1d6e561`),
  `research/diagnostic-generalization` (`33f3702`).
- Experiment branches are **not merged into `main`**; only `main`'s own docs are
  there. `main` does not contain EXP-002…PHASE2 records.
- **Finding:** `README.md` and `user_data/configs/README.md` are **stale** (see
  A17).
- Remote `origin` = `https://github.com/asdramxrt-oss/freqtrade-pa-momentum-research.git`
  — **returns 404; the GitHub repository does not exist**, so no push is possible
  (carried from prior phases).

## A2. Project structure

```
research/            preregistration, hypotheses, experiment_specs, experiment_results, decisions, walk_forward, notion_map
user_data/
  strategies/shared/ pa_indicators, pa_signals, pa_structure, pa_pullback, pa_risk
  strategies/turtle/ DonchianTurtleBaseline.py
  strategies/pullback/ PullbackContinuation.py  (3 classes)
  configs/           EXP-001..EXP-003 (4 configs)
  scripts/           download_data.ps1, run_experiment.ps1, exp002..exp004 runners, diagnostics/
  data/              git-ignored candles (spot + futures mirror)
ml/                  empty scaffolding only (turtle, pullback, breakout_retest, volatility_expansion, features, labels, validation)
reports/             empty (README only)
tests/unit/          7 test files
docs/                created by this audit
```

**Created but empty:** `ml/*`, `reports/`, `research/walk_forward/`,
`tests/integration/`, `tests/research/`.

## A3. Strategies present

| Family | File | Classes | Status |
|--------|------|---------|--------|
| Turtle / Donchian | `strategies/turtle/DonchianTurtleBaseline.py` | long-only | EXP-001 FAIL (frozen reference) |
| Pullback continuation | `strategies/pullback/PullbackContinuation.py` | `PullbackContinuation` (both), `PullbackContinuationLong`, `PullbackContinuationShort` | EXP-003 MIXED, EXP-004 FAIL |

Only **two** strategy families implement `IStrategy`. `breakout_retest` and
`volatility_expansion` are hypothesised (`research/hypotheses/`) but **not
implemented**.

## A4. Research code and shared library

Pure, causal, **no freqtrade import**: `pa_indicators`, `pa_signals`,
`pa_structure`, `pa_pullback`, `pa_risk`. Strategies wire them to the engine.
Diagnostics in `user_data/scripts/diagnostics/` (Phase 2). Runners:
`exp002_cost_sweep.py`, `exp003_backtest.py`/`geometry`/`complementarity`,
`exp004_oos.py`/`regression`. No notebook, no ad-hoc script outside these.

## A5. Data pipeline

- `user_data/scripts/download_data.ps1` → `freqtrade download-data`, spot, 4h,
  default `20190101-20260101`.
- **On disk:** 10 spot 4h feathers (`BTC…DOT`, 2019→2026-09-16 for most) plus a
  **futures mirror** produced by `prepare_futures_data.py` (byte-identical OHLCV).
- **Not present:** 1h/1d data, `funding_rate`, `mark`, `index`, `premiumIndex`,
  `open_interest`. freqtrade **supports** these candle types
  (`--candle-types … funding_rate, mark, open_interest, premiumIndex`) — carry/
  basis/OI research is feasible but requires a download step.
- No trade-tick data (`--dl-trades` unused).

## A6. Features / FreqAI

- **No FreqAI model, no feature engineering, no `ml/` code.** `ml/README.md`
  documents intent (second-stage filter per setup) and hygiene rules.
- `freqtrade.freqai` **imports successfully**.
- Installed ML libs: **scikit-learn 1.9.0, XGBoost 3.3.0, PyTorch 2.13.0+cpu,
  TA-Lib 0.7.1, SciPy 1.17.1, statsmodels 0.14.6, optuna 4.9.0**.
  **Missing: LightGBM, CatBoost** (common FreqAI defaults) — would need install
  if selected.

## A7. Backtesting infrastructure

- freqtrade CLI backtesting, `--cache none`, `--export trades`.
- Custom runners summarise into `research/experiment_results/*.json`.
- **No walk-forward harness** (`research/walk_forward/` is an empty README).
- **No Monte-Carlo / bootstrap harness** in repo (Phase-2 diagnostics added
  bootstrap + permutation as one-offs).
- **No hyperopt run** anywhere; optuna installed but unused.

## A8. Exchange / market configuration

- Exchange **Binance** only; **spot** for EXP-001 and `EXP-003-spot-long`;
  **futures isolated 1×** for EXP-003 long/short/combined and EXP-004.
- **Margin mode is NOT supported by the Binance class** in this freqtrade build
  (only SPOT and FUTURES); this forced the futures-mirror workaround.
- No API keys (empty); `dry_run: true`; API server disabled.

## A9. Timeframe / universe

- **4h only.** 10 USDT pairs: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, AVAX, DOT.
- `StaticPairList` (explicit whitelist) everywhere; no dynamic filters.
- Listing starts differ (SOL/AVAX/DOT from 2020-08/09; DOGE 2019-07).

## A10. Sizing / leverage / stops / exits

- Sizing: `custom_stake_amount` = `equity × 0.01 / (2×ATR) × price`, capped at
  equity (1% risk per trade).
- Max open trades 5; no pyramiding.
- **Leverage = 1.0** (default; no `leverage()` override, no leverage in configs).
- **Stops:** fixed `2×ATR(20 at entry)` via `custom_stoploss` + `-30%` backstop.
- **Exits:** Donchian-10 channel exit; `minimal_roi = {}` (ROI disabled);
  `exit_profit_only = False`.
- **Trailing:** none. **Protections:** none configured. **Position adjustment:**
  disabled.

## A11. Fees / slippage

- Fee 0.05% per side (base); stress 0.20% used in EXP-001/002.
- **Slippage is not modelled natively**; represented only as a higher fee
  (protocol documents this). No spread/impact model.
- **Funding is excluded** from all futures results (no funding data; mirror
  candles).

## A12. Hyperoptimization

None. No `hyperopt` config, no `Hyperopt` class, no results. optuna present but
unused. This is consistent with the charter (no parameter optimisation in the
baseline programme).

## A13. Walk-forward

**Not built.** Documented plan only: anchored 3y in-sample / 1y OOS / 1y step,
and a rule that only strategies passing A1–A8 may enter. No strategy has passed,
so it has never run.

## A14. Experiment framework

- `research/preregistration/research_charter.md` + `experiment_protocol.md`
  (both FROZEN) define universe, periods, costs, A1–A8 thresholds.
- `research/experiment_specs/EXP-00N.md` frozen before runs; results in
  `research/experiment_results/EXP-00N.{md,json}`; decisions in
  `research/decisions/DECISION_LOG.md` (DEC-001…DEC-006).
- Templates exist (`TEMPLATE.md`).

## A15. Reports / Notion / GitHub integration

- `reports/` empty. Notion hierarchy documented in `README.md` and
  `research/notion_map.md`; live pages exist for `00…08` sections and the
  Experiments database, plus EXP-001…004 rows and a PHASE 2 page (created last
  phase under `08 — Architecture`).
- `research/notion_map.md` maps experiment IDs → Notion URLs → Git artifacts.
- GitHub: **blocked** (repo 404).

## A16. Experiment status (recorded, from `DECISION_LOG.md`)

| Exp | Subject | Verdict |
|-----|---------|---------|
| EXP-001 | Turtle/Donchian baseline | **FAIL** (4/8; p=0.066, OOS −18.98%, DD 61.6%) |
| EXP-002 | Turtle internal transaction costs | **FAIL** (same criteria; costs not the cause) |
| EXP-003 | Pullback continuation | **MIXED** (combined FAIL, short FAIL, long-only 8/8 on dev + 2025) |
| EXP-004 | Frozen long pullback fresh OOS (2026) | **FAILS FRESH OOS** (PF 0.607, −12.75%, 64 trades) |
| PHASE 2 | Diagnostic of generalization failure | Knowledge only: **multiple plausible explanations** |

## A17. Known bugs, debt and inconsistencies

1. **`README.md` is stale:** claims "76 tests passing" (actual **124 test
   functions / 133 collected**); lists EXP-002/003/004 as `PLANNED`; lists
   `breakout_retest`/`volatility_expansion` folders that **do not exist**;
   baseline paragraph predates EXP-002+.
2. **`user_data/configs/README.md` is stale:** documents only `EXP-001.json`
   (four more configs exist).
3. **`main` is behind reality:** EXP-002…PHASE2 live only on research branches.
4. **Empty scaffolding** (`ml/`, `reports/`, `walk_forward/`, integration tests)
   can be mistaken for implemented capability.
5. **No funding/mark/OI data** while the objective mentions futures carry/basis —
   a data gap, not a code bug.
6. **LightGBM/CatBoost absent** (ML capability gap if selected).
7. **Slippage modelled only via fee** (documented limitation).
8. **GitHub repo missing** (no off-machine backup).
9. **No `docs/` directory** prior to this audit.
10. **Charter sequence divergence:** charter lists EXP-004 as "Turtle + Pullback"
    but EXP-004 was re-scoped (DEC-005) — correctly recorded, but the charter
    table itself is now knowingly out of date for that row.

## A18. Correctness posture (verified, not assumed)

- 124 test functions; `pytest tests -q` → **133 passed**; `ruff check`/`format`
  clean.
- Causality enforced by prefix-invariance tests and a pivot **publication delay**.
- Strategy code provably unchanged vs frozen commits (`git diff` empty; SHA-256
  recorded in PHASE2).
- Deterministic reproduction verified (EXP-001/003/004 numbers reproduced
  exactly during PHASE2).

## A19. What the objective asks for vs what exists

| Objective component | Exists now | Gap |
|---------------------|-----------|-----|
| Turtle breakout baseline | Yes | fails validation; long-only |
| Complementary price-action strategies | Pullback only | breakout-retest, volatility-expansion unimplemented |
| ML where justified | No | no features/labels/models; libs partially present |
| Regime awareness | No | diagnostic knowledge only |
| Robust risk management | Partial | 1% ATR sizing, no portfolio/leverage/protections |
| Realistic Binance futures costs | Partial | fee-only; no funding/slippage/spread |
| Strong OOS validation | Yes (per-experiment) | no walk-forward harness, no Monte-Carlo suite |
| Production-safe Freqtrade impl | Baseline only | no production checklist executed |

## A20. Audit conclusion

The repository is a **clean, well-governed research project** with two strategy
families, one shared causal library, a frozen protocol, and an honest record of
failures. It is **research-grade, not production-grade**. The largest genuine
gaps for the stated objective are: (1) no walk-forward / Monte-Carlo harness,
(2) no funding/slippage cost model, (3) no implemented complementary strategies
beyond pullback, (4) no ML layer, and (5) stale top-level documentation.

**No production code was changed by this audit.** Next phase (B) is deep research
recorded in Notion, per the workflow.
