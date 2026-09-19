# Phase D — Critical evaluation of the research

**Question:** should any component beyond the Turtle baseline be implemented?
**Answer at this date:** **no component is yet justified by evidence.** Every
candidate remains a hypothesis pending its preregistered experiment.

Categories are kept strictly separate: FACT / INTERPRETATION / HYPOTHESIS /
UNKNOWN.

---

## Post-execution addendum (2026-09-16) — does not rewrite the evaluation above

This evaluation was written **before** any Phase-3 experiment ran. Three have now
executed, so several of its questions have answers. The original text is left
intact; this addendum records the delta.

- **F5 update.** Genuine Binance USDT-M futures OHLCV **is now on disk**
  (`user_data/data_p3`: 4h OHLCV + 1h mark + funding). SI-1 is resolved; the spot
  mirror is no longer the basis of Phase-3 results.
- **Critical question 1** (Turtle on genuine futures) — **answered**: FAIL both
  directions (P3-EXP-001); costs are not the cause (P3-EXP-002).
- **Critical question 2** (carry independently useful) — **answered for the
  implemented proxy**: FAIL; the single-leg trailing-sign carry paid funding
  (P3-EXP-003). Not a general refutation of carry.
- **Critical question 5** (volatility estimator) — **still open**; now the
  lowest-complexity next experiment (P3-EXP-006).
- **Critical question 6** (regime) — **still open**, but PHASE 2's regime-shift
  evidence makes P3-EXP-007 the most directly motivated test.
- **Critical questions 3/4/7/8/9** — still open; no component has shown robust
  incremental OOS value.
- **Architecture table** — unchanged conclusion strengthened: **Turtle-only
  remains the default; every other architecture is still UNRESOLVED, now with
  three failed Phase-3 experiments behind the "no evidence" column.**

Full audit and proposed next steps: `.mece/cells/CELL-002/REPORT.md`,
`.mece/cells/CELL-003/REPORT.md`, `.mece/SYNTHESIS.md`.

---

## FACT (directly established)

**Internal, measured**
- F1. Turtle (spot, long-only): development PF ≈ 1.37, but full-sample
  expectancy not significant (p=0.066), 2025 OOS −18.98% (PF 0.80), wallet DD
  61.6% → **FAILED** the frozen criteria (`EXP-001.md`).
- F2. Costs degrade Turtle monotonically but are **not** the primary cause
  (`EXP-002.md`).
- F3. Pullback long was positive on development + 2025 but **failed fresh 2026
  OOS** (64 trades, PF 0.607, −12.75%); short and combined failed (`EXP-004.md`).
- F4. PHASE 2 diagnostics: 2026 had materially lower volatility/range/dispersion;
  Turtle breakout follow-through (ATR-normalised, market-relative) did **not**
  deteriorate; the consumed 2025 pullback result turns **negative without its top
  3 winners**; holdout bootstrap CIs include zero (`PHASE2_*`).
- F5. Data: `funding_rate`/`mark`/`index`/`premiumIndex` are downloaded for the 10
  perps; **open-interest history is unavailable**; the on-disk futures OHLCV is a
  **spot mirror** (`docs/DATA_AVAILABILITY.md`). Genuine Binance USDT-M futures
  OHLCV **is obtainable** (verified via ccxt, 2026-09-16).
- F6. No strategy in this project has ever passed the frozen validation criteria.

**External, verified**
- F7. Time-series momentum is documented (Moskowitz/Ooi/Pedersen 2012, *JFE*
  104:228) **but** Kim/Tse/Wald (2016) attribute much of it to **volatility
  scaling**, not the signal.
- F8. Residual momentum roughly doubles risk-adjusted profit in **equities**
  (Blitz/Huij/Martens 2011, *JEF* 18:506).
- F9. Crypto market/size/momentum factors exist (Liu/Tsyvinski/Wu 2022, *JF* 77),
  **but** a near-identical cross-sectional study on the same Binance perp universe
  under purged walk-forward **failed** (Fayez Junior 2026).
- F10. Crypto carry/basis is well documented (Cao/Zhai/Luo 2024; arXiv 2212.06888;
  "The Crypto Carry Trade"), with explicit exchange-solvency risk.
- F11. Range-based volatility estimators are ~5–8× more efficient, **but
  Garman–Klass beats Yang–Zhang**, which is often worst (*Empirical Economics*
  2026).
- F12. Purged K-fold CV + embargo, triple-barrier labels and meta-labelling are
  established methods (López de Prado 2018) — a methods source, not evidence of
  alpha.

## INTERPRETATION (what the facts reasonably suggest)

- I1. The prior programme's apparent edges behaved like **regime- and right-tail-
  dependent** effects rather than stable edges (F1, F3, F4).
- I2. Trend following's documented performance may be **partly a sizing effect**;
  our tests must therefore separate signal from sizing (F7).
- I3. Carry/basis is the **strongest documented orthogonal** exposure and is now
  data-feasible here (F10, F5) — but its published Sharpes embed arbitrage and
  exchange assumptions that our single-leg, retail-cost, exchange-risk setting
  does not share.
- I4. Cross-sectional momentum is **high risk here**: the closest prior attempt on
  this exact venue and instrument class failed (F9).
- I5. Sophistication is not self-justifying: the volatility-estimator literature
  explicitly shows simpler estimators beating complex ones (F11).
- I6. The only honest evaluation path now is **purged walk-forward**, because the
  2025 and 2026 holdouts are no longer pristine (F5/F6 + registry).

## HYPOTHESIS (requires empirical test — not belief)

- H1. Turtle has a small positive edge on genuine futures with a short side.
- H2. Residual momentum transfers from equities to crypto perps.
- H3. Carry/basis survives realistic costs and exchange risk on this universe.
- H4. Regime information improves selection/sizing/risk.
- H5. ML improves trade *selection* from a validated baseline.
- H6. A more efficient volatility estimator improves sizing enough to matter.

## UNKNOWN (cannot currently be established)

- U1. Whether **any** candidate adds robust incremental value OOS. (No Phase-3
  experiment has run.)
- U2. The true net-of-cost, exchange-adjusted carry return on this universe.
- U3. Whether residual momentum is better than total-return momentum in crypto.
- U4. Whether a **pristine** holdout exists — it does not; it requires new data.
- U5. The realised slippage/spread for these perps at our order sizes.

---

## The nine critical questions

**1. Is Turtle itself robust?**
FACT: spot long-only failed (F1); costs not the cause (F2). UNKNOWN: futures long,
short, and signal-vs-sizing (U1). Verdict: **unproven; must be tested on genuine
futures OHLCV before anything is layered on it.**

**2. Is carry independently useful?**
FACT: strongly documented externally (F10); data now available (F5).
UNKNOWN: net-of-cost, exchange-risk-adjusted result here (U2). Verdict:
**promising hypothesis, not established.** Test standalone (P3-EXP-003).

**3. Is residual momentum transferable from equities to crypto?**
FACT: equity evidence is strong (F8); crypto momentum factors exist (F9); a close
crypto cross-sectional attempt failed. UNKNOWN: transferability (U1/U3). Verdict:
**explicit transferability hypothesis; do not assume.**

**4. Does cross-sectional momentum overlap too heavily with Turtle?**
UNKNOWN — must be measured empirically by return/trade/exposure correlation
(P3-EXP-005). Not inferable from names.

**5. Does volatility estimation improve trading decisions?**
FACT: estimator efficiency differs (F11); UNKNOWN: whether it improves trading
(then it must be measured as a trading result, not an estimation result). Verdict:
**test ATR vs GK only (P3-EXP-006); YZ excluded.**

**6. Does regime classification improve OOS results?**
UNKNOWN. PHASE 2 documented a regime shift but explicitly did **not** justify a
filter. Verdict: **test, do not assume (P3-EXP-007); reject if it removes
profitable trades or destabilises OOS.**

**7. Does ML add incremental value?**
UNKNOWN. Methods exist (F12); no evidence yet that ML helps here. Verdict: **test
last, on a validated baseline, identical-candidate-trade ablation (P3-EXP-008);
disable if it does not help.**

**8. Does combining strategies diversify?**
UNKNOWN — must be measured (return correlation, trade overlap, exposure overlap,
drawdown overlap), not inferred (P3-EXP-005).

**9. Is complexity justified?**
Per component: the only justification accepted is **robust incremental OOS value
on identical candidate trades**. "It might help" is a hypothesis, not a
requirement. Current count of components meeting that bar: **zero**.

---

## Architecture selection (STEP 6) — current status

The candidate architectures (A Turtle-only … G selected components) **cannot yet
be ranked or selected**, because no Phase-3 experiment has produced evidence.

| Architecture | Evidence for | Evidence against | Status |
|--------------|--------------|------------------|--------|
| A. Turtle only | only implemented, simplest; nothing else validated | failed spot long-only criteria | **current default** |
| B. + complementary momentum | equity evidence | crypto cross-sectional prior failure | UNRESOLVED |
| C. + carry | strong external evidence, data feasible | exchange risk, cost uncertainty | UNRESOLVED |
| D. + momentum + carry | diversification hypothesis | both unresolved | UNRESOLVED |
| E. + regime | PHASE 2 regime shift observed | no filter evidence | UNRESOLVED |
| F. + ML | methods available | no value evidence | UNRESOLVED |
| G. selected components | would follow evidence | none yet | UNRESOLVED |

**Rule that applies regardless:** if the evidence ultimately supports only Turtle,
the architecture stays **Turtle only**. No component is added to look
sophisticated.

## Conclusion

**No architecture is selected, and no component is justified yet.** The correct
next action is to *execute the preregistered experiments* (which requires their
research implementations) under the frozen specification, then re-run this
evaluation with results. Until then, the system remains **Turtle-only (frozen,
unmodified)**.
