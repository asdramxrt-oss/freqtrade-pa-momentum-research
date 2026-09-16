# PHASE 2 — Diagnostic analysis of generalization failure

| Field | Value |
|-------|-------|
| **Phase** | 2 (diagnostic — no strategy change) |
| **Branch** | `research/diagnostic-generalization` |
| **Status** | PLANNED |
| **Frozen subjects** | Turtle `DonchianTurtleBaseline` @ `12acbf7`; Pullback long `PullbackContinuationLong` @ `c4bee8e` |
| **Inputs (read-only)** | EXP-001…EXP-004 records |

## 1. Objective

Explain, with evidence, why the historical/2025 performance of the Turtle
breakout baseline and of the long-only pullback-continuation strategy failed to
generalise to the fresh 2026 holdout. **The output is knowledge, not a strategy.**
No rule, parameter, filter, indicator, pair set or model may be changed or added.

## 2. Hypotheses under investigation (not conclusions)

- **H1 Regime change** — 2026 differs from the development period in realised
  volatility, trend persistence, range width, or dispersion.
- **H2 Trend/breakout follow-through** — breakouts and pullback confirmations are
  followed by less continuation in 2026 than in development.
- **H3 Concentration** — historical performance depended on a small number of
  trades, pairs, or years.
- **H4 Distribution shift** — the per-trade return distribution of 2026 differs
  from development beyond sampling noise.
- **H5 Cost / frequency** — trade frequency or edge-per-trade moved relative to
  fees.
- **H6 Data quality** — a data defect could explain part of the difference.
- **H7 Sampling variation** — the differences are consistent with noise and the
  fresh window is too short to decide.

These are tested descriptively; several may be simultaneously true.

## 3. Frozen strategy versions (must not change)

| Subject | Commit | SHA-256 |
|---------|--------|---------|
| `DonchianTurtleBaseline.py` | `12acbf7` | `5A841A1307E68DF53EFFF89CB7D01BEF8E5518F73FC996314F9E81D6A96D9C03` |
| `PullbackContinuation.py` | `c4bee8e` | `750616345F17F59AC621F4946577B0883EFB26C9285BC9719FBEB9B1DD6E58D4` |
| `pa_pullback.py` | `c4bee8e` | `EEF725BD298CB642C2C6F4E19F6DE5D5BC616C465BA0EBE3D41935740BD975E9` |
| `pa_structure.py` | `c4bee8e` | `4413BF2FC5530AFB76136285E0A08797ECBF4DCBF57CAD1D7A23348F638FDF86` |

Diagnostics **read** these modules (signal definitions are reused as-is) and
**never edit** them. Any discovered semantics-changing bug is reported and the
phase stops.

## 4. Periods

| Label | Range | Role |
|-------|-------|------|
| **D** DEVELOPMENT | 2019-01-01 → 2025-01-01 | pre-holdout history |
| **C** CONSUMED OOS | 2025-01-01 → 2026-01-01 | used by EXP-001/002/003 |
| **F** FRESH OOS | 2026-01-01 → 2026-09-16 | used by EXP-004 (fresh) |
| **P** POOLED REFERENCE | 2019-01-01 → 2026-01-01 | EXP-001/003 headline; **not independent** |

C and F are never pooled with D and presented as independent evidence. P is
reported only as a reference and labelled non-independent.

## 5. Metrics (exact definitions)

**Market regime (per pair, then aggregated per period across the 10 pairs):**
realised volatility = std of 4h log returns; ATR(20)/close; Donchian(20)
width/close (range width); efficiency ratio (Kaufman) over 20 bars =
`|close[t]-close[t-20]| / Σ|Δclose|`; lag-1 return autocorrelation; sign
continuation probability `P(sign(r_t)=sign(r_{t-1}))`; mean run length of
same-sign returns; cross-sectional dispersion = std across pairs of the 4h return
per bar; large-move frequency = fraction of bars with `|r_t| > 4×ATR%_t`.

**Breakout follow-through (Turtle signal definition, read-only):** for each
frozen `first_breakout_up` bar `t` (entry assumed at `close[t]`), forward return,
MFE and MAE over horizons {1,3,6,12,24,48} bars; immediate-failure rate
(`close[t+1] < close[t]` and `close[t+3] < close[t]`).

**Pullback geometry (frozen `pullback_continuation_frame`, long side):** the
existing geometry columns (impulse ATR, pullback depth ATR/%, duration, distance
from structure, trigger margin, confirmation body) plus forward MFE/MAE over
{6,12,24,48} bars from the signal bar; geometry compared across periods and
between forward-positive and forward-negative signals.

**Trade-level (frozen strategies re-run deterministically for diagnostics only):**
trades, net return, PF, expectancy, win rate, avg/median trade, std, skew,
wallet max drawdown, holding time, MAE/MFE (from `min_rate`/`max_rate`),
top-1%/5%/10% profit contribution, contribution of the single largest winner,
win/loss magnitude ratio, and the same after removing the largest 1/3/5 winners
(descriptive sensitivity only).

**Stability:** per-year and per-month trade/return/PF/expectancy matrices; per-pair
trades/return/PF/win-rate/PNL-contribution. No pair is removed.

**Costs:** turnover, fees paid, fees as % of gross PnL, edge-per-trade vs fee.

## 6. Tests to perform

1. Data-quality audit (gaps, duplicates, monotonicity, timezone, spot↔futures
   mirror equality, final-candle completeness, listing starts).
2. Market-regime comparison table D/C/F (all metrics above).
3. Breakout follow-through comparison D/C/F.
4. Pullback geometry + post-signal excursion comparison D/C/F.
5. Trade-distribution / concentration comparison D/C/F.
6. Entry-timing (first-N-bar) and holding-period comparison D/C/F.
7. Pair and cross-asset stability.
8. Cost diagnostic (EXP-002 methodology, no new fee sweep).
9. Statistics: bootstrap 95% CI for mean per-trade return per strategy×period;
   permutation test of D vs F per-trade returns. Tests are limited to this small,
   pre-specified set to limit multiple-comparison inflation.
10. Research-lineage / implicit-selection audit from the committed record.

## 7. Interpretation rules

- Every statement is labelled **OBSERVED FACT**, **POSSIBLE EXPLANATION**, or
  **UNPROVEN HYPOTHESIS**.
- No threshold may be chosen to make a failed strategy profitable, and no
  condition may be derived that would have avoided 2026 losses.
- Volatility/regime bins, where used, are quantiles computed independently of
  strategy outcomes.
- If evidence is mixed or thin, the conclusion is "multiple plausible
  explanations" or "insufficient evidence" — never a forced single cause.
- No claim of permanent strategy decay without sufficient evidence.

## 8. Prohibited activities (explicit)

Modifying Turtle or Pullback logic/parameters/exits/stops; removing or adding
pairs; changing timeframe; adding indicators, filters, regime or ML; hyperopt or
any parameter search; fitting thresholds to improve results; using 2026 results to
alter the strategies; combining the strategies; building a router; cherry-picking
periods; extending the OOS. No new strategy is created.

## 9. Deliverables

- `research/experiment_results/PHASE2_DIAGNOSTIC.md` (report)
- machine-readable outputs `PHASE2_*.json`
- diagnostic scripts under `user_data/scripts/diagnostics/`

## 10. Limitations

- The fresh window is ~8.5 months; several tests are under-powered.
- Re-running frozen strategies for trade-level diagnostics is deterministic and
  must reproduce EXP-001/EXP-003/EXP-004 numbers exactly; any mismatch is a bug to
  report, not to tune.
- Diagnostic re-runs do not constitute new out-of-sample evidence.
- Correlation is not causation; regime statements are descriptive.
