# PHASE 2 — Diagnostic analysis of generalization failure

| Field | Value |
|-------|-------|
| **Phase** | 2 (diagnostic — no strategy change) |
| **Branch** | `research/diagnostic-generalization` |
| **Specification** | `research/experiment_specs/PHASE2_DIAGNOSTIC.md` (`1085045b0c6415180d94a16a4913981e4d31cac3`) |
| **Results commit** | `eab0b242cab146f92e0e3e6e26a54559ea6c459e` |
| **Frozen subjects** | Turtle `12acbf7`; Pullback long `c4bee8e` (unchanged, hashes verified) |
| **Run date** | 2026-09-16 |
| **Status** | COMPLETED |

Every statement below is labelled **OBSERVED FACT**, **POSSIBLE EXPLANATION**, or
**UNPROVEN HYPOTHESIS**. No strategy, parameter, pair, threshold, filter or model
was changed. No new strategy was created.

## 1. Objective

Explain with evidence why Turtle and long-only pullback continuation failed to
generalise to the fresh 2026 holdout.

## 2. Frozen subjects (verified unchanged)

| Subject | Commit | SHA-256 (still current) |
|---------|--------|-------------------------|
| `DonchianTurtleBaseline.py` | `12acbf7` | `5A841A13…D9C03` |
| `PullbackContinuation.py` | `c4bee8e` | `75061634…E58D4` |
| `pa_pullback.py` | `c4bee8e` | `EEF725BD…975E9` |
| `pa_structure.py` | `c4bee8e` | `4413BF2F…DF86` |

`git diff 12acbf7 -- user_data/strategies/turtle` and
`git diff c4bee8e -- user_data/strategies/pullback user_data/strategies/shared`
are both empty. Diagnostics read the frozen signal definitions and re-ran the
frozen strategies **deterministically for measurement only**; the pooled
re-runs reproduce the recorded experiment numbers exactly (Turtle pooled: 1,347
trades / PF 1.228; Pullback pooled: 607 / 1.567; Pullback 2025: 88 / 1.338;
Pullback fresh 2026: 64 / 0.607 = EXP-004).

## 3. Periods

| Label | Range | Role |
|-------|-------|------|
| **D** Development | 2019-01-01 → 2025-01-01 | 6.0 yr |
| **C** Consumed OOS | 2025-01-01 → 2026-01-01 | 12 mo |
| **F** Fresh OOS | 2026-01-01 → 2026-09-16 | 8.5 mo |
| **P** Pooled (reference) | 2019-01-01 → 2026-01-01 | non-independent |

## 4. Data-quality findings (`PHASE2_data_quality.json`)

**OBSERVED FACT**

- 10 pairs; **0 duplicate timestamps**, all series monotonic, all timezone-aware UTC.
- The **futures mirror is byte-identical to spot** for all 10 pairs
  (`max_abs_diff = 0`).
- Total missing 4h bars: **32**, all inside the development period (7 pairs, ≤5
  bars each). **The 2025 and 2026 windows have zero missing bars.**
- Per-pair listing histories differ as expected (SOL/AVAX/DOT start 2020-08/09).

**Conclusion:** data quality is **not** a plausible cause of the 2026 failure.

## 5. Core summary table (`PHASE2_trade_diagnostics.json`)

Return is net USDT (compounding-era development trades are far larger in
absolute size, so cross-period USDT is directional only; PF/expectancy are the
comparable statistics).

| Metric | Turtle D | Turtle C (2025) | Turtle F (2026) | Pullback D | Pullback C (2025) | Pullback F (2026) |
|--------|---------:|----------------:|----------------:|-----------:|------------------:|------------------:|
| Trades | 1,153 | 180 | 123 | 516 | 88 | 64 |
| Profit factor | 1.373 | 0.796 | 0.861 | 1.645 | 1.338 | 0.607 |
| Net return (USDT) | +580,088 | −1,898 | −879 | +62,195 | +1,403 | −1,276 |
| Expectancy (USDT) | +503.11 | −10.54 | −7.15 | +120.53 | +15.94 | −19.94 |
| Win rate | 31.8% | 27.2% | 26.0% | 31.0% | 36.4% | 25.0% |
| Wallet max DD | 61.5% | 39.6% | 33.5% | 28.6% | 14.4% | 24.9% |
| Market change | +3,804% | −34.3% | −27.5% | +3,804% | −34.3% | −27.5% |
| p-value | 0.014 | 0.317 | 0.662 | 0.016 | 0.389 | 0.164 |

**OBSERVED FACT:** both strategies had statistically significant positive
expectancy **only** in development. Neither was positive in either holdout.

## 6. Market-regime comparison (`PHASE2_market_regimes.json`)

Median across the 10 pairs:

| Metric | D | C (2025) | F (2026) |
|--------|--:|---------:|---------:|
| Realised vol (4h) | 0.0219 | 0.0183 | **0.0130** |
| ATR% | 0.0311 | 0.0269 | **0.0200** |
| Donchian width (norm.) | 0.145 | 0.133 | **0.095** |
| Efficiency ratio (20) | 0.232 | 0.235 | 0.228 |
| Return autocorr (lag-1) | −0.027 | +0.009 | **+0.037** |
| Sign continuation | 0.469 | 0.508 | 0.477 |
| Mean run length | 2.71 | 3.02 | 2.79 |
| Cross-sectional dispersion | 0.0108 | 0.0074 | **0.0055** |
| Market return (median) | +2,438% | −36.9% | −26.3% |

**OBSERVED FACT:** 2026 had **materially lower realised volatility, smaller ATR%
and narrower Donchian ranges** (~60%, ~64%, ~65% of development respectively),
**lower cross-sectional dispersion**, and **slightly higher** return
autocorrelation. Trend-efficiency and sign-continuation were essentially
unchanged.

**OBSERVED FACT:** Development was a large **bull** regime (median +2,438%);
both holdouts were **bear** regimes (−36.9%, −26.3%). Both strategies are
long-only, so the holdout direction is a structural headwind.

## 7. Breakout follow-through (`PHASE2_turtle_followthrough.json`)

Median across pairs; ATR-normalised because the strategy risks a fixed 2×ATR:

| Metric | D | C (2025) | F (2026) |
|--------|--:|---------:|---------:|
| Signals | 4,337 | 798 | 494 |
| Immediate fail (1 bar) | 0.522 | 0.526 | 0.546 |
| Forward return @24 bars (raw) | +1.80% | +0.02% | +0.02% |
| Forward return @24 bars (ATR) | 0.752 | 0.184 | **0.479** |
| MFE @24 bars (ATR) | 3.76 | 3.25 | **4.19** |
| MAE @24 bars (ATR) | −2.60 | −3.04 | −2.97 |
| Market-relative excess @24 bins (mean of pair means) | +0.00123 | −0.00103 | **+0.00145** |

**OBSERVED FACT:** raw forward returns and MFE shrank in 2026 in **absolute**
terms, but once normalised by ATR the 2026 breakout follow-through is
**comparable to development and better than 2025**, and market-relative
follow-through (excess) in 2026 is **positive** — the highest of the three
periods at 24 and 48 bars.

**POSSIBLE EXPLANATION:** Turtle's 2026 failure is **not** explained by
breakouts failing to follow through. The mechanic still "worked" relative to the
market; the loss came from the long-only book in a falling market (beta), not
from a collapse of breakout behaviour.

**UNPROVEN HYPOTHESIS:** whether a short side or a different exit would have
converted that relative follow-through into profit — untested and out of scope.

## 8. Pullback geometry and relative edge (`PHASE2_pullback_geometry.json`)

Signal-level (all frozen long signals, not just traded):

| Metric | D | C (2025) | F (2026) |
|--------|--:|---------:|---------:|
| Signals | 660 | 132 | 90 |
| Forward-positive (24 bars) | 336/324 (52%) | 69/63 (52%) | **28/60 (32%)** |
| Impulse (ATR, median) | 4.14 | 4.01 | 4.16 |
| Pullback depth (ATR, median) | 1.008 | 1.036 | 1.035 |
| Pullback bars (median) | 5 | 5 | 5 |
| Distance from structure (ATR) | 3.26 | 3.04 | 3.12 |
| Mean forward return @24 | +3.03% | +1.37% | **−1.51%** |
| Mean market-relative excess @24 | **+1.16%** | **+0.43%** | **−0.38%** |

**OBSERVED FACT:** the **geometry of the setup is essentially identical** across
periods (confirming EXP-003's "winners and losers are geometrically similar" at
the signal level). What changed is the **outcome**: the market-relative
(excess-over-universe) 24-bar return went from +1.16% (D) to +0.43% (C) to
**−0.38% (F)**.

**POSSIBLE EXPLANATION:** the pullback setup retained a small positive relative
edge through 2025 but **lost it in 2026**; the fresh-window failure is not merely
market beta.

## 9. Trade distribution and concentration (`PHASE2_trade_diagnostics.json`)

| Metric | Turtle D | Turtle C | Turtle F | Pullback D | Pullback C | Pullback F |
|--------|---------:|---------:|---------:|-----------:|-----------:|-----------:|
| Skew of trade PnL | 5.64 | 3.65 | 5.31 | 6.64 | 2.60 | 2.76 |
| Largest winner / gross profit | 4.1% | 13.8% | **26.6%** | 9.3% | **15.8%** | **24.5%** |
| Top 5% of trades / gross profit | 63.8% | 54.7% | 71.0% | 63.4% | 51.9% | 68.6% |
| Net if top 3 winners removed | +363,240 | −4,117 | −3,706 | +32,759 | **−571** | −2,456 |
| Win/loss magnitude ratio | 2.94 | 2.13 | 2.45 | 3.66 | 2.34 | 1.82 |

**OBSERVED FACT (the single most important concentration finding):** the
**consumed 2025 Pullback result was fragile** — its +1,403 USDT net becomes
**−571 USDT when the three largest winners are removed**, and one trade supplied
15.8% of gross profit. The 2025 "+14.01%" is therefore driven by a very small
number of trades.

**OBSERVED FACT:** all series are strongly right-skewed (5–7) in development and
remain so in the holdouts; in 2026 a single winner was 24–27% of gross profit for
both strategies.

**POSSIBLE EXPLANATION:** the historical edge is a small-winner-count,
right-tail phenomenon; a short holdout can easily miss the few trades that carry
the result. This is consistent with the observed failure to replicate.

## 10. Entry timing and holding period

**OBSERVED FACT (holding, from trade diagnostics):** median trade duration fell
across periods for both strategies — Turtle 4,080 → 3,120 → 2,640 min
(68h → 52h → 44h); Pullback 3,840 → 3,720 → 3,000 min. In **every** period,
winners were held far longer than losers (e.g. Turtle F: 7,800 min vs 1,920 min).
The trend-following "let winners run" mechanic behaved identically.

**OBSERVED FACT (entry timing):** breakout immediate-failure rate rose only
slightly (52.2% → 52.6% → 54.6%). Pullback confirmation body size shrank
(median 1.67% → 1.71% → 1.09%) and trigger margin shrank (0.198 → 0.204 → 0.180
ATR), i.e. confirmations were slightly weaker in 2026, but not dramatically.

**POSSIBLE EXPLANATION:** entry timing did not break; the holding mechanic did
not break. Shorter durations are consistent with lower volatility, not with a
changed strategy behaviour.

## 11. Pair and cross-asset behaviour

**OBSERVED FACT (profitable pairs):** Turtle 2025 2/10, Turtle 2026 6/10;
Pullback 2025 5/10, Pullback 2026 3/10. No single pair was uniformly to blame,
and the pair sets that worked differ between 2025 and 2026 (Turtle 2025:
BNB/LINK; Turtle 2026: ETH/LINK/XRP; Pullback 2025: BNB/DOGE/LINK;
Pullback 2026: LINK/DOT/BTC).

**OBSERVED FACT:** cross-sectional dispersion fell from 0.0108 (D) to 0.0055 (F),
i.e. **pairs moved more together** in 2026 — less idiosyncratic opportunity.

**POSSIBLE EXPLANATION:** the 2026 failure is **market-wide rather than
pair-specific**; no pair-removal rule would address it (and none was applied).

## 12. Transaction-cost findings (`PHASE2_trade_diagnostics.json`)

**OBSERVED FACT:** fees are a small share of activity: Turtle D 57,873 USDT,
Turtle F 315 USDT; Pullback D 3,843 USDT, Pullback F 169 USDT. Turnover fell with
trade count. The 2026 Turtle loss (−879 USDT) is far larger than its fees (315
USDT).

**Conclusion:** consistent with EXP-002 — ordinary costs are **not** the cause.

## 13. Statistical findings (`PHASE2_statistics.json`)

Bootstrap 95% CI of the mean per-trade profit (USDT); permutation test for a
difference in means; small pre-specified test set.

| Strategy | Period | n | Mean | 95% CI | Excludes 0? |
|----------|--------|--:|-----:|--------|:-----------:|
| Turtle | D | 1,153 | +503.11 | [115.90, 928.74] | **Yes** |
| Turtle | C 2025 | 180 | −10.54 | [−30.15, 11.05] | No |
| Turtle | F 2026 | 123 | −7.15 | [−35.27, 27.41] | No |
| Pullback | D | 516 | +120.53 | [29.48, 227.50] | **Yes** |
| Pullback | C 2025 | 88 | +15.94 | [−17.72, 53.17] | No |
| Pullback | F 2026 | 64 | −19.94 | [−44.76, 9.57] | No |

Permutation tests (D vs F; C vs F): Turtle diff +510.26, p = 0.42 / −3.40,
p = 0.86; Pullback diff +140.47, p = 0.31 / +35.87, p = 0.155.

**OBSERVED FACT:** development means are positive with CIs excluding zero; **all
holdout CIs include zero**; the **2025-vs-2026 difference is not statistically
significant** for either strategy.

**Limitation:** absolute-USDT returns are heteroskedastic across eras; the tests
are directional and under-powered. No multiple-comparison adjustment beyond
restricting to this small set.

## 14. Research-lineage / selection audit (`PHASE2_lineage.json`)

**OBSERVED FACT:** the EXP-003 specification was frozen (`a07e966`) **before**
implementation and any run; parameters were a-priori round values, no hyperopt
was run; long/short/combined were pre-registered variants with **combined** as
the primary object. The 2025 OOS was reported **within** EXP-003, and the
long-only variant was then promoted to leading candidate after the combined
variant failed. EXP-004 fixed the fresh window and decision rule before running.

**POSSIBLE EXPLANATION:** the 2025 result was not the product of an explicit
search, but it carries the selection weight of **one holdout on one of three
variants**, and §9 shows it was **concentrated in a few trades**. Its evidential
weight is low-to-moderate, not confirmatory.

## 15. Potential explanations

| Potential explanation | Evidence | Strength |
|-----------------------|----------|----------|
| **Market regime change** | 2026 vol ≈ 60% of D, ranges ≈ 65%, dispersion ≈ 51%; both holdouts bear vs development bull | **Supported (observed)** |
| **Trend persistence change** | Efficiency ratio 0.232/0.235/0.228; autocorr slightly higher in F; Turtle ATR-normalised and market-relative follow-through **better** in F | **Not supported** |
| **Volatility change** | Large drop, but Turtle follow-through normalises to ≈ D; Pullback relative edge fell | **Partially supported** |
| **Entry timing change** | Immediate-fail 52.2→54.6%; weaker pullback confirmation body/margin | **Weak** |
| **Trade concentration** | Pullback 2025 turns negative without top 3 winners; 2026 largest winner 24–27% of gross | **Supported (observed)** |
| **Pair dependence** | Profitability shifts across pairs; no consistent culprit; dispersion fell | **Weak / market-wide** |
| **Cost effects** | Fees ≪ losses; turnover fell | **Not supported** |
| **Data-quality issue** | No duplicates/gaps in 2025–2026; mirror identical | **Not supported** |
| **Sampling variation** | Holdout CIs include zero; C-vs-F difference insignificant; right-skewed returns | **Strongly supported** |
| **Permanent strategy decay** | No evidence beyond two short bear holdouts | **Unproven** |

Multiple explanations are simultaneously supported; none alone is decisive.

## 16. Interpretation

**OBSERVED FACTS**

1. Both strategies were significantly positive only in development; every
   holdout mean is statistically indistinguishable from zero.
2. 2026 had materially lower volatility, narrower ranges and lower dispersion,
   and was a bear market; trend efficiency was unchanged.
3. Turtle breakout follow-through, normalised by ATR and to the market, was
   **not** worse in 2026 (it was better than 2025). Its failure is consistent
   with long-only beta in a falling market rather than a broken breakout edge.
4. The pullback setup geometry is stable across periods, but its
   market-relative forward return turned **negative** in 2026.
5. The consumed 2025 Pullback result was **concentrated**: it becomes negative
   without its three largest winners.
6. Data quality and ordinary costs are not explanations.

**POSSIBLE EXPLANATIONS**

- The development edge was partly a **bull-market / high-volatility** effect
  (regime), and/or a **small-winner-count right-tail** effect that a short
  holdout is unlikely to reproduce (sampling). Both are consistent with the data.
- The pullback setup additionally lost a small positive **relative** edge in
  2026, whereas the breakout's relative edge did not.

**UNPROVEN HYPOTHESES**

- That either strategy has permanently stopped working.
- That a regime/volatility filter, short side, or different exit would have made
  2026 profitable (explicitly not tested).

## 17. Limitations

- The fresh window is ~8.5 months and under-powered; several tests cannot
  distinguish noise from a real shift.
- Development trades are absolute-USDT and heteroskedastic across eras.
- Only two holdouts exist; 2025 and 2026 were both bear markets, so direction is
  confounded with the passage of time.
- Diagnostic re-runs are deterministic reproductions of recorded experiments and
  are not new out-of-sample evidence.

## 18. Final decision

**B. MULTIPLE PLAUSIBLE EXPLANATIONS.**

The evidence supports **sampling variation / trade-concentration** and a
**market-regime shift (volatility compression and a long-only bear holdout)** as
simultaneous, mutually compatible explanations, with a smaller role for a lost
pullback *relative* edge in 2026. The evidence **does not** support a breakout
follow-through collapse, cost effects, or data problems, and it is **insufficient
to claim permanent strategy decay**.

No new strategy, filter, parameter, or combination is proposed here. A future
research phase should be designed around whether the development edge is
regime-dependent and right-tail dependent — as a hypothesis to be tested on new
data, not as a rule fitted to 2026.

## 19. Reproduction

```powershell
$env:PYTHONPATH = "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop"
python user_data/scripts/diagnostics/diagnose_data_quality.py
python user_data/scripts/diagnostics/diagnose_market_regimes.py
python user_data/scripts/diagnostics/diagnose_turtle_followthrough.py
python user_data/scripts/diagnostics/diagnose_pullback_geometry.py
python user_data/scripts/diagnostics/diagnose_trades.py
python user_data/scripts/diagnostics/diagnose_statistics.py
```
