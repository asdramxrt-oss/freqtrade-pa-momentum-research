# CELL-002 — P3 Experiment Audit

| Field | Value |
|-------|-------|
| **Cell** | CELL-002 |
| **Status** | COMPLETED |
| **Audit date** | 2026-09-16 |
| **Branch** | `research/diagnostic-generalization` |
| **HEAD at audit** | `5c3d4fbf90c3ec9aaf82129803647052fa62da88` |
| **Method** | Read-only audit of committed artifacts; no experiment was re-run (per TASK.md). Machine-readable JSONs cross-checked against the result documents. |
| **Production code touched** | No |

---

## 1. Scope

Audit `research/experiment_results/`, `research_lib/`, `user_data/configs/`,
`user_data/scripts/`, and the relevant `docs/`, then state what repository
evidence actually demonstrates for **P3-EXP-001, P3-EXP-002 and P3-EXP-003**.
Separate measured results, methodology, interpretation and unresolved questions;
check lookahead, train/test contamination, cost assumptions, sample-size,
robustness and reproducibility.

## 2. Artifacts inspected

Committed research artifacts:

- `research/experiment_results/P3-EXP-001.md` / `.json` / `.raw.json`
- `research/experiment_results/P3-EXP-002.md` / `.json` / `.raw.json`
- `research/experiment_results/P3-EXP-003.md` / `.json` / `.raw.json`
- `research/experiment_results/P3_FUTURES_DATA_MANIFEST.json`
- `docs/EXPERIMENT_REGISTRY.md`, `docs/ISSUES_LOG.md`, `docs/DATA_AVAILABILITY.md`
- `docs/FROZEN_IMPLEMENTATION_SPEC.md`, `docs/PHASE_D_CRITICAL_EVALUATION.md`
- `research/preregistration/experiment_protocol.md`, `research_charter.md`
- `research/decisions/DECISION_LOG.md`
- `research_lib/strategies/TurtleFuturesResearch.py`, `FundingCarryResearch.py`
- `user_data/strategies/shared/pa_indicators.py` (causality contract)
- `user_data/configs/P3-EXP-001.json`, `P3-EXP-003.json`
- `user_data/scripts/p3_exp001_run.py`, `p3_exp002_costs.py`, `p3_exp003_carry.py`
- `user_data/data_p3/futures/` (60 feathers: 10 pairs × 6 candle types)

## 3. Measured results (OBSERVED FACT — from committed JSON/raw JSON)

Cross-checked each `.md` table against its `.raw.json`; all matched to the
recorded precision.

**P3-EXP-001 (genuine `data_p3` futures, funding applied, fee 0.05%)**

| Arm | Window | Trades | PF | Net % | Wallet DD % | p | Funding |
|-----|--------|-------:|----:|------:|------------:|--:|--------:|
| long_vol | full | 1325 | 1.149 | +1462.3 | 57.0 | 0.1922 | applied |
| long_vol | test (2025–2026) | 306 | **0.813** | −27.5 | 44.7 | 0.2691 | applied |
| long_raw | full | 1482 | **1.503** | +216.3 | **14.0** | **0.0020** | applied |
| long_raw | test | 389 | **0.852** | −13.6 | 26.4 | 0.2982 | applied |
| short_vol | test | 314 | 0.924 | −11.5 | 34.9 | 0.6430 | applied |
| short_raw | test | 376 | 0.974 | −2.4 | 20.2 | 0.8579 | applied |

Signal-vs-sizing ablation confirmed: fixed notional dominates volatility-scaled
sizing on PF (1.503 vs 1.149), drawdown (14.0% vs 57.0%) and significance
(p=0.0020 vs 0.1922).

**P3-EXP-002 (cost grid, full sample, funding applied)**

| Arm | 0.05% | 0.10% | 0.15% | 0.20% | 0.25% | **0.35% stress** |
|-----|------:|------:|------:|------:|------:|----------------:|
| long_vol PF | 1.149 | 1.124 | 1.102 | 1.082 | 1.065 | **1.037** |
| long_raw PF | 1.504 | 1.458 | 1.415 | 1.373 | 1.333 | **1.259** |

Test-window at stress: long_vol PF 0.627, long_raw PF 0.662. **Acceptance is
mixed by sizing**: `long_raw` ≥ 1.05, `long_vol` < 1.05.

**P3-EXP-003 (carry, funding applied)**

| Window | Trades | PF | Net % | p | Funding PnL (USDT) |
|--------|-------:|----:|------:|--:|-------------------:|
| full | 428 | 1.348 | +495.9 | 0.1601 | **−11,306** |
| test | 159 | **0.805** | −20.7 | 0.4049 | +205 |

The engine-reported funding PnL is stored as
`funding_fees_applied_usdt = −11305.87` in `P3-EXP-003.raw.json`, matching the
−11,306 figure.

## 4. Methodology

- Frozen signal reused from the pure shared modules (Donchian entry 20 / exit 10,
  ATR 20, 2×ATR stop, ROI off, 1× leverage). Research strategies live in
  `research_lib/strategies/` and do not import, modify or subclass the production
  strategy.
- Periods: full `20190908-20260916`; train `→20221231`; validation
  `20230101-20241231`; test `20250101-20260916` (recorded non-pristine).
- P3-EXP-002 is a pre-registered grid (fee × slippage) collapsed to six unique
  effective per-side costs because freqtrade models slippage through the fee
  parameter; base 0.05%, stress 0.35%.
- P3-EXP-003 signal is the sign of the trailing 3-day mean funding rate; the
  funding-receiving side is held; rebalance daily; equal notional = 10% equity per
  active pair; exit = funding-sign flip; no directional stop (recorded
  limitation).

## 5. Risk checks

| Check | Finding | Evidence |
|-------|---------|----------|
| **Lookahead** | PASS — Donchian channels are shifted one bar (`pa_indicators.rolling_high/low` `shift=1`); ATR is Wilder-smoothed and causal; carry uses `merge_asof(direction="backward")` on funding. | `user_data/strategies/shared/pa_indicators.py:118-177`; `FundingCarryResearch.py:93-106` |
| **Train/test contamination** | PASS — no hyperopt; fixed frozen parameters; sequential windows; the test window is labelled non-pristine in every artifact. No parameter was chosen from the test window. | registry hard constraints; result docs §3 |
| **Cost assumptions** | PASS / CONSERVATIVE — base 0.05%/side, stress 0.35%/side; funding applied from real 1h-mark data. Slippage is a flat per-side adder, not a spread/impact model (limit). | P3-EXP-002 §3; `ISSUES_LOG.md` SI-4 |
| **Sample size** | ADEQUATE for a verdict, thin for inference — OOS trades 306/389/159; carry validation only 100 trades. | raw JSON |
| **Robustness** | LIMITED — one universe (10 perps), one timeframe (4h), one non-pristine test window; no walk-forward; no parameter plateau test. | registry; result docs §7 |
| **Reproducibility** | PASS — deterministic commands recorded in each raw JSON; machine-readable raw results committed; JSONs match the `.md` tables. | `P3-EXP-00*.raw.json` |

## 6. Defects found and fixed in this cell

| # | Defect | Fix |
|---|--------|-----|
| 1 | `research/experiment_results/P3-EXP-002.md` header said **`COMPLETED → PASS`** while the document's own SI-4 correction and `P3-EXP-002.json` (`verdict = "FAIL"`) say FAIL. | Corrected the status header; marked the pre-correction §5 verdict and §8 decision as superseded. Result numbers unchanged. |
| 2 | `research/experiment_results/P3-EXP-001.md` §8 stated "Funding is not yet applied" although the corrected run at the top of the file applies funding. | Reworded the limitation to point at the superseded/corrected distinction. |
| 3 | `docs/EXPERIMENT_REGISTRY.md` was stale: header said "none executed", the table said P3-EXP-001 `PARTIAL` / 002/003 `NO`, and the multiple-testing ledger said 0 experiments run — contradicting three committed, executed experiments. | Updated the header, the three table rows, the ledger counts, and added an SI-4 execution note. The registry's own rule #4 requires the ledger to be updated as experiments run. |

No measured result, raw JSON, strategy parameter, config or test was altered *by
this cell*. The doc edits only reconcile labels with the committed evidence.
(The wave's other repairs — formatter fix, `conftest.py` bootstrap discovery and
the diagnostics double-count fix — are recorded in `.mece/WAVE.md` and touch no
strategy logic and no measured result.)

## 7. Established vs uncertain

**Established (measured):**
1. Genuine-futures Turtle fails OOS: long arms PF 0.813 / 0.852 on the
   2025–2026 window; short negative throughout.
2. Costs are not the binding constraint (full-sample PF ≥ 1.05 to 0.35%/side for
   `long_raw`), but `long_vol` fails the stress criterion (1.037 < 1.05).
3. Volatility-scaled sizing produces a larger compounded headline but worse PF,
   far worse drawdown, and non-significant expectancy vs fixed notional.
4. The carry implementation did **not** earn funding (net funding PnL −11,306
   USDT) and failed OOS (PF 0.805); its full-sample PF is directional, not carry.

**Weak / uncertain:**
- All test windows are non-pristine and only ~20 months long.
- Carry validation PF 2.41 rests on 100 trades.
- No walk-forward or parameter-plateau evidence exists.

**Unsupported assumptions (not to be relied on):**
- That any of these three results transfers to a pristine future window.
- That carry is refuted in general; only this naive trailing-sign, single-leg
  implementation is refuted.

## 8. Verification commands performed

```powershell
git status; git branch --show-current; git log --oneline -10
python -c "import json; ..."                 # cross-check .md tables vs .raw.json / .json
python -m pytest tests -q                    # 133 passed
python -m ruff check .                       # All checks passed
python -m ruff format --check .              # 86 files already formatted (final pass; 84 at cell time)
```

JSON cross-check results: all P3 PF/net/trade/p-value figures matched the `.md`
tables; `P3-EXP-003.raw.json` funding PnL = −11305.87; `P3-EXP-001/002/003.json`
`funding_applied = true`; `P3-EXP-002.json verdict = "FAIL"`;
`P3-EXP-001.raw.json` contains 16 runs, `P3-EXP-003.raw.json` 4 runs.

### 8.1 Post-wave reconciliation (final integrity pass)

This report separates its evidence cleanly:

- **Facts observed before repairs** — §3 (measured results) and §5 (risk checks),
  read from the committed artifacts.
- **Repairs performed by the wave** — §6 (three doc-label defects reconciled;
  no measured result, raw JSON, strategy, config or test altered).
- **Final verification state** — recorded below.

The final post-wave tree is **intentionally not clean**: the eight research repair
targets (including `P3-EXP-001.md`, `P3-EXP-002.md` and `EXPERIMENT_REGISTRY.md`)
plus `WAVE.md`/`SYNTHESIS.md` are modified, and the cell reports are untracked.
Final verification: `pytest tests -q` → **133 passed**; `ruff check .` clean;
`ruff format --check .` clean (**86 files already formatted** — the count tracks
the new MECE Markdown artifacts, which ruff also formats; the cell-time count
was 84 and the wave's own close recorded 87, while the final integrity pass
observes 86 in the frozen post-wave tree). Frozen production strategy diff:
**zero lines**. No
Phase-3 experiment was executed by this audit or the wave; only Phase-2
diagnostics were re-run for reproduction.

## 9. Remaining blockers / residual research risk

- **No pristine holdout.** 2025 and 2026 are consumed; a genuine holdout requires
  post-2026-09 data accrual (SI-2, open).
- **Uneven maturity.** P3-EXP-004A/004B/005/006/007/008 remain unimplemented
  (SI-3, open). The registry now reflects this accurately.
- **Single-leg carry only.** No delta-neutral cash-and-carry exists; the carry
  verdict applies to the implemented proxy only.
- **Flat slippage model.** No spread/impact or market-impact modelling.
- **Power.** Short, overlapping, same-direction (bear) holdouts confound regime
  with time.
- **Notion mirror not updated.** `docs/EXPERIMENT_REGISTRY.md` is declared the Git
  source of truth; the corresponding Notion DB was not edited in this cell.

## 10. OpenCode session ID

Not exposed by the execution environment in this session.
