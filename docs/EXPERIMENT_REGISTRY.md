# Phase 3 — Experiment Registry (Git mirror)

Mirror of the Notion **Phase 3 — Experiment Registry** database
(`collection://c2c4f6e5-47ad-477a-b360-8bfce6add095`). Git is the executable
source of truth; Notion is the human-readable control plane.

**Status: P3-EXP-001, P3-EXP-002 and P3-EXP-003 have been EXECUTED** (verdicts:
FAIL / FAIL / FAIL). All other experiments remain PREREGISTERED and **not**
executed. No production strategy code has been written or modified; Phase-3
implementations live in `research_lib/strategies/` and results under
`research/experiment_results/`.

**DEC-007 (diagnostic-only, no verdict):** a walk-forward harness
(`research/walk_forward/run_walk_forward.py`, frozen windows in
`walk_forward_config.json`) was applied to the already-failed P3-EXP-001 long
arms and P3-EXP-003 carry, implementations unchanged, strictly to measure
stability/decay/reproducibility. It is **not** a new strategy experiment and
does **not** change any verdict; 2025–2026 windows are NON-PRISTINE.

## Naming and scope

- New IDs use the **`P3-` prefix** because `EXP-001…EXP-015` are already taken by
  the *closed original programme* (and `EXP-001…004` have other meanings).
- The original Notion `Experiments` database **could not be altered** via the API
  (`ADD COLUMN` fails with a schema parse error), so a dedicated Phase-3 registry
  was created instead of mutating the historical record.
- Universe everywhere: 10 Binance USDT perpetuals — BTC, ETH, BNB, SOL, XRP, ADA,
  DOGE, LINK, AVAX, DOT. Timeframe everywhere: 4h.

## Registry

| ID | Experiment | Executable now | Missing data / dependency |
|----|-----------|----------------|---------------------------|
| P3-EXP-001 | Real futures Turtle baseline (long + short; signal vs vol-scaled sizing) | EXECUTED | **FAIL** — genuine `data_p3` futures OHLCV (funding + 1h mark); both long arms negative OOS (PF 0.813 / 0.852), short negative throughout. `research/experiment_results/P3-EXP-001.md` |
| P3-EXP-002 | Turtle cost / slippage sensitivity | EXECUTED | **FAIL (corrected)** — stress PF 1.037 (`long_vol`, below the 1.05 threshold) vs 1.259 (`long_raw`); costs are not the cause of failure. `research/experiment_results/P3-EXP-002.md` |
| P3-EXP-003 | Carry / basis standalone | EXECUTED | **FAIL** — net funding PnL −11,306 USDT (paid funding, did not harvest it); OOS PF 0.805. `research/experiment_results/P3-EXP-003.md` |
| P3-EXP-004A | Cross-sectional momentum | NO | research candidate implemented in `research_lib/strategies/CrossSectionalMomentumResearch.py` with dry-run config `user_data/configs/P3-EXP-004A.json`; not backtested/validated because local Freqtrade is blocked by the Pydantic dependency mismatch |
| P3-EXP-004B | Residual momentum | NO | code not written; genuine futures OHLCV |
| P3-EXP-005 | Turtle + complementary momentum | NO | depends on 001 and 004A/B |
| P3-EXP-006 | Volatility estimator ablation (ATR vs GK; YZ excluded) | NO | estimator code not written |
| P3-EXP-007 | Regime (selection / sizing / allocation) | NO | regime code not written |
| P3-EXP-008 | ML meta-filter (tested LAST) | NO | ML pipeline not written; LightGBM not installed (sklearn/XGBoost available) |
| DEC-007 | Diagnostic-only walk-forward of already-failed engines (non-strategy) | EXECUTED | **DIAGNOSTIC ONLY** — P3-EXP-001 long arms + P3-EXP-003 carry, implementations unchanged; windows frozen in `research/walk_forward/walk_forward_config.json`; 2025–2026 windows NON-PRISTINE. Not a verdict. `research/experiment_results/DEC-007_WALK_FORWARD.md` |

**Execution note (2026-09-16).** P3-EXP-001/002/003 were first run when funding
was silently excluded (engine requires 1h mark; SI-4). After the 1h-mark data was
downloaded, all affected runs were re-executed with funding applied; the earlier
numbers are superseded, not deleted (see `docs/ISSUES_LOG.md` SI-4 and each
result document's correction section). P3-EXP-002's verdict changed from PASS to
FAIL as a result.

Every record in Notion carries the full preregistration: research question, both
hypotheses, baseline, treatment, dataset, universe, period, timeframe, features,
parameters, entry/exit logic, sizing, leverage, fees, slippage, funding treatment,
train/validation/test periods, walk-forward method, leakage controls, metrics,
acceptance criteria, failure criteria, status and result.

## Hard constraints recorded in every record

1. **Genuine futures OHLCV must not be silently replaced by the spot mirror.**
   Genuine Binance USDT-M futures candles are obtainable (verified via ccxt
   `fetch_ohlcv`, 2026-09-16) but are **not on disk**; the on-disk
   `futures/*-futures.feather` files are a spot mirror kept for EXP-003/004
   reproduction.
2. **2025–2026 are not pristine.** They were already observed by EXP-001…004 and
   PHASE 2. Any test/OOS using them is recorded as non-pristine; a genuinely
   pristine holdout requires new post-2026-09 accrual.
3. **Open-interest data is unavailable** (Binance `openInterestHist` historical
   `startTime` rejected), so no OI candidate is testable here.
4. **No parameter search.** Values are the classic/round preregistered values.
5. **ML is last** and only on a validated baseline.
6. **A component that does not show robust incremental OOS value is removed.**

## Acceptance / failure criteria (all experiments)

Acceptance requires **all** of: positive OOS expectancy with bootstrap CI
excluding 0; sufficient trades (≥200 full-sample / ≥100 OOS); wallet max DD < 35%;
≥60% of years positive; no single pair > 50% of PnL; PF ≥ 1.05 at 0.20% fee;
parameter plateau (not a spike); leakage tests pass; no single-period dependence;
economic rationale consistent with behaviour.

Failure = any of: OOS expectancy ≤ 0; PF < 1.00 at base; < 100 OOS trades; one
pair > 50% of PnL; one year > 60% of PnL; PF < 1.00 at 0.20%; wallet DD ≥ 35%;
leakage detected. **Otherwise: INSUFFICIENT EVIDENCE** (not PASS).

---

# Multiple-testing ledger (STEP 4)

## Counts

| Dimension | Count so far | Notes |
|-----------|--------------|-------|
| Phase-3 hypotheses preregistered | 9 experiments (EXECUTED: 3) | P3-EXP-001…008 (004 split A/B); 001–003 run, all FAIL |
| Prior-programme experiments run | 4 (+1 diagnostic phase) | EXP-001…004, PHASE 2 |
| Strategy families implemented | 2 rule-based + 2 Phase-3 research engines | Turtle, Pullback; `research_lib` adds futures Turtle + funding carry |
| Parameter variants searched (Phase 3) | 0 | no search performed; fixed frozen parameters |
| Different datasets used | spot OHLCV + spot-derived mirror + genuine futures (`data_p3`) | genuine futures now used for P3-EXP-001/002/003 |
| Pair combinations tested | 1 fixed universe (10 pairs) | no pair subsets selected |
| Timeframe variants | 1 (4h) | 1d untested |
| Model variants (ML) | 0 | ML not started |
| Diagnostic robustness runs (non-strategy, DEC-007) | 1 | walk-forward of P3-EXP-001/003; diagnostic only, no strategy tested, no parameter selected |
| Consumed holdouts | 2025 and 2026 | **not pristine** |

## Data-snooping risk statement

- The prior programme consumed the **2025** holdout (EXP-001/002/003) and the
  **2026** holdout (EXP-004). Any reuse of those windows is no longer pristine and
  is explicitly labelled.
- Nine Phase-3 experiments and their treatments constitute a **family of tests**.
  If all are run against the same data, the probability that at least one looks
  good by chance rises materially. Controls:
  1. every experiment is preregistered with a fixed treatment (no variant search);
  2. acceptance requires *multiple* dimensions, not one metric;
  3. results that pass only on total profit / PF / one year / one pair are not
     passes;
  4. the ledger above is updated as experiments run; the number of tests is
     reported alongside every conclusion;
  5. a genuinely pristine holdout requires **new data**, not re-slicing.
- No result may be selected as "the best" across this family without disclosing
  the family size and the selection.
