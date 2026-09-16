# FROZEN IMPLEMENTATION SPECIFICATION

**Programme:** Freqtrade PA Momentum Research — Phase 3
**Status:** FROZEN on 2026-09-16
**Scope:** defines *exactly* what may be implemented for the Phase-3 experiments,
and what the production system is until evidence changes it.
**Production change authorised by this document:** **NONE.** The production
system remains the frozen Turtle baseline, unmodified. This document authorises
*research implementations* only, and only the ones enumerated here.

> FROZEN means frozen. It is not edited because a later result is inconvenient.
> If implementation exposes a genuine error here, STOP, record a
> `SPECIFICATION ISSUE`, and request approval before changing anything.

---

## 1. System objective

Determine — by preregistered experiment — the **smallest** cryptocurrency
futures trading system for which robust, cost-surviving, out-of-sample evidence
exists. Components are added only when they show robust **incremental** value on
identical candidate trades; otherwise they are removed. If nothing beats the
baseline, the system stays the baseline.

## 2. Supported markets and instruments

- Exchange: **Binance** only.
- Instrument: **USDT-margined perpetual futures**.
- Universe (fixed, no selection): **BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK,
  AVAX, DOT** (10 pairs).
- Leverage: **1.0** everywhere. No higher leverage is authorised.
- Margin: isolated.

## 3. Data sources

| Data | Source | Status |
|------|--------|--------|
| Genuine futures OHLCV | Binance USDT-M via freqtrade/ccxt | **to be downloaded (verified obtainable 2026-09-16)**; the existing spot mirror must NOT be used as a substitute |
| `funding_rate`, `mark`, `index`, `premiumIndex` | Binance, downloaded | present (perp listing → 2026-09-16) |
| Open interest | Binance | **unavailable** — no OI component may be implemented |
| Spot OHLCV | Binance | present (used only for historical reproduction of EXP-001…004) |

Data governance: raw data is git-ignored; every run records the exact timerange,
pair set, timeframe and data revision.

## 4. Timeframes

- Primary: **4h**.
- 1d is **not** authorised unless a future preregistration requires it.

## 5. Reference baseline (frozen, unchanged)

`DonchianTurtleBaseline` at commit `12acbf7`, unmodified:
entry `close > prior 20-bar high` (shift 1, rising edge); exit
`close < prior 10-bar low`; stop **2×ATR(20)** + −30% backstop; ROI disabled;
risk 1% of equity per trade; max 5 open; no pyramiding; long-only in the existing
implementation.

**A short-capable Turtle variant and a volatility-scaled sizing variant are
authorised as research implementations** (required by P3-EXP-001), built as
**separate research strategy classes**; the baseline class is not edited.

## 6. Research engines authorised by this specification

Each engine implements exactly the preregistered definition in the Phase-3
registry. All are causal and use the fixed values below. **No parameter search is
authorised for any engine.**

### 6.1 P3-EXP-003 — Carry / funding harvest
- Signal: sign of trailing **3-day mean funding** per pair.
- Position: single-leg perpetual on the funding-**receiving** side.
- Rebalance: **daily**; flip when the signal sign flips.
- Sizing: equal notional per active pair; gross exposure cap = 1× equity.
- No threshold on funding magnitude.

### 6.2 P3-EXP-004A — Cross-sectional momentum
- Rank the 10 pairs by trailing **30-day** return; long **top 3**, short
  **bottom 3**; equal notional per leg.
- Rebalance every **7 days** at a fixed bar.
- Exactly one variant (no vol-normalised variant unless preregistered later).

### 6.3 P3-EXP-004B — Residual momentum
- Market benchmark = equal-weight universe return.
- Rolling OLS `r_i = α + β·r_mkt + e` over a **90-day** window, estimated **only**
  on data strictly before the ranking date.
- Residual signal = cumulative residual over **30 days**; long top 3 / short
  bottom 3; weekly rebalance.

### 6.4 P3-EXP-006 — Volatility estimator
- Compare **ATR(20)** vs **Garman–Klass(20)** as the stop/sizing input.
- **Yang–Zhang is NOT authorised** (documented reason: 2026 literature shows it
  often worst despite complexity). Parkinson optionally, only if preregistered.

### 6.5 P3-EXP-007 — Regime
- States: terciles of realised volatility and terciles of efficiency ratio,
  computed **independently of strategy outcomes**, causally.
- Applied to (a) selection, (b) sizing, (c) allocation, tested **separately**.
- Boundaries fixed on train/validation only.

### 6.6 P3-EXP-008 — ML meta-filter (last)
- Type: **meta-labelling** — a binary classifier deciding whether to act on an
  existing baseline trade. Never a trade generator.
- Features: frozen causal set (setup geometry, volatility, funding); no future
  information.
- Labels: triple-barrier, horizon recorded; purge+embargo = label horizon.
- Validation: purged K-fold CV inside each walk-forward training window; threshold
  fixed on validation; probability **calibration** reported.
- Model: a single pre-declared model (gradient boosting) with fixed
  hyperparameters and a recorded seed. LightGBM is **not installed**; use
  scikit-learn / XGBoost. No model or feature search.

## 7. Entry / exit / stop / sizing (all engines)

- Exits and stops follow each engine's definition; where an engine reuses the
  Turtle mechanics, they are the frozen Turtle values.
- Position sizing: 1% risk at the stop distance for Turtle-family engines; equal
  notional for cross-sectional/carry engines (as above). No adaptive sizing
  unless it is the object of the experiment.
- Funding is applied from real data to any held perpetual position.

## 8. Costs (frozen scenarios)

| Scenario | Fee/side | Slippage/side |
|----------|----------|---------------|
| base | 0.05% | 0.00% |
| mid | 0.10% | 0.05% |
| stress | 0.20% | 0.15% |

Scenarios are preregistered and are never chosen after seeing results.

## 9. Validation methodology (frozen)

- Partitions: train 2019-01-01→2022-12-31; validation 2023-01-01→2024-12-31;
  test/OOS 2025-01-01→2026-09-16 — **labelled NON-PRISTINE** (already observed by
  EXP-001…004/PHASE 2).
- Walk-forward: anchored expanding, 1-year OOS, 1-year step.
- Purge + embargo by label horizon for any labelled/overlapping work.
- A genuinely pristine holdout requires **new post-2026-09 data**; it cannot be
  manufactured by re-slicing.
- Causality tests (prefix invariance, pivot publication delay) must remain green.

## 10. Acceptance and failure criteria

Acceptance requires **all**: positive OOS expectancy with bootstrap CI excluding
0; ≥200 full-sample and ≥100 OOS trades; wallet max DD < 35%; ≥60% of years
positive; no single pair > 50% of PnL; PF ≥ 1.05 at 0.20% fee; parameter plateau;
leakage tests pass; no single-period dependence; economic rationale consistent.

Failure = any of: OOS expectancy ≤ 0; PF < 1.00 at base; < 100 OOS trades; one
pair > 50% of PnL; one year > 60% of PnL; PF < 1.00 at 0.20%; wallet DD ≥ 35%;
leakage detected. **Otherwise INSUFFICIENT EVIDENCE** — never "PASS by profit".

## 11. Components explicitly REJECTED (must not be implemented)

- **Router / portfolio allocator** — no validated components exist; charter
  forbids using a router to rescue weak strategies.
- **Open-interest signals** — data unavailable.
- **Yang–Zhang volatility estimator** — evidence favours simpler estimators.
- **Alternative bar sampling (dollar/volume/imbalance)** — no evidence; tick data
  absent.
- **Fractional differentiation** — only within a selected ML feature pipeline, and
  only if it shows lift; otherwise rejected.
- **Adaptive/optimised parameters, hyperopt, threshold search** — not authorised.
- **Short side of the baseline / leverage > 1** — not authorised beyond the
  research variants named in §5.
- **Any component not listed in §6.**

## 12. Production safeguards

- Research code lives outside the production strategy; the production Turtle class
  is not edited.
- No live trading. `dry_run: true`, empty credentials, API server disabled.
- Every result is committed with its experiment ID and config; Notion mirrors it.
- A component may enter production only after: experiment passes §10 → Phase-D
  re-evaluation → an explicit production-readiness stage → a superseding frozen
  specification.

## 13. Current production system (until superseded)

**Turtle-only, frozen at `12acbf7`, unmodified.** This document does not change
it.

---

## SPECIFICATION ISSUES

- **SI-1 (open):** genuine futures OHLCV is not on disk; the first implementation
  step for P3-EXP-001 must download and review it, and must not silently use the
  spot mirror. Awaiting no approval to *download* (data only), but any resulting
  result is void if the mirror is used.
- **SI-2 (open):** no pristine OOS exists; results using 2025–2026 are
  non-pristine by construction and will be labelled as such.
- **SI-3 (open):** the Phase-3 experiments require research implementations that do
  not yet exist; this specification authorises only those in §6, and implementation
  may begin only after human approval of this document.
