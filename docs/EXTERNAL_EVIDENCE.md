# External evidence register (Phase 3)

Verified references supporting the Phase-B research. Every entry was located and
confirmed via search on 2026-09-16; **no citation is asserted from memory**. Each
entry records the claim, the source, and its applicability/limitations for *this*
project (Binance USDT perpetuals, 4h, 10 majors, long/short).

Labels: **FACT** (published result), **INTERPRETATION** (our reading),
**APPLICABILITY** (what it means here).

---

## 1. Time-series momentum (trend following)

**FACT.** Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", *Journal of
Financial Economics* 104(2):228–250, DOI `10.1016/j.jfineco.2011.11.003`.
Documents significant time-series momentum (TSMOM) across 58 futures for 1–12
month horizons, with a diversified portfolio showing little exposure to standard
factors and performing best in extreme markets.

**FACT (important counter-evidence).** Kim, Tse & Wald (2016), "Time series
momentum and volatility scaling", *Journal of Financial Markets* (ScienceDirect
`S1386418116301379`). Finds MOP's result is **largely driven by volatility
scaling (risk parity) rather than by momentum itself**; unscaled TSMOM is
statistically similar to buy-and-hold, and cross-sectional momentum has higher
alpha than unscaled TSMOM.

**APPLICABILITY.** Trend following is supported in the literature, **but a large
part of the documented outperformance may come from volatility scaling, not the
signal**. Our Turtle already uses ATR-based scaling, so a future test must
separate the *signal* from the *sizing* (ablation) rather than attributing the
result to "trend".

**FACT.** Jegadeesh & Titman (1993) — cross-sectional momentum (foundational).
**FACT.** Asness, Moskowitz & Pedersen (2013), "Value and Momentum Everywhere",
*Journal of Finance* 68:929–985.
**FACT.** Novy-Marx (2012), "Is momentum really momentum?", *JFE*.

## 2. Residual momentum

**FACT.** Blitz, Huij & Martens (2011), "Residual Momentum", *Journal of
Empirical Finance* 18(3):506–521, DOI `10.1016/j.jempfin.2011.01.003`.
Ranking on residual (factor-adjusted) returns rather than total returns roughly
**doubles risk-adjusted profits**, is more consistent over time, is less
concentrated in the cross-section extremes, and is nearly market-neutral
(positive even in recessions, +5.6% p.a.).

**APPLICABILITY.** Strengthens the *hypothesis* that residual momentum could be
orthogonal to absolute trend following — but the evidence is **equities, monthly,
1963–2009/2010**. It is **not** crypto evidence and must not be assumed to
transfer. Rolling-beta estimation introduces look-ahead risk that must be
controlled.

## 3. Cryptocurrency momentum / cross-section

**FACT.** Liu, Tsyvinski & Wu (2022), "Common Risk Factors in Cryptocurrency",
*Journal of Finance* 77(2):1133–1177, DOI `10.1111/jofi.13119` (NBER w25882).
A three-factor model — market, size, **momentum (3-week)** — captures the
cross-section of crypto returns.

**FACT.** "A Trend Factor for the Cross Section of Cryptocurrency Returns",
*Journal of Financial and Quantitative Analysis* (2024), DOI
`10.1017/S0022109024000747`. A cross-sectional CTREND factor is reported to
dominate momentum in that sample.

**FACT (directly relevant negative evidence).** Fayez Junior (2026), "Failure of
Cross-Sectional Alpha Screening on Cryptocurrency Perpetual Futures: A
Quantitative Post-Mortem Using OHLCV and Funding Rate Signals", SSRN
`10.2139/ssrn.6701738`. On **ten USDT-margined Binance perpetuals** with daily and
intraday price/volume/funding signals, under a **purged walk-forward** framework:
naive linear IC −0.0097 (t=−1.54), orthogonal linear IC −0.0102, XGBoost ranker
IC +0.0243 yet **net Sharpe −2.91, max DD −95.6%**. Concludes the employed signals
contain no exploitable cross-sectional alpha at the 8h horizon.

**APPLICABILITY.** Crypto cross-sectional momentum exists in academic samples,
but a **very close prior attempt — same exchange, same instrument class, similar
universe, purged walk-forward — failed decisively**. Cross-sectional candidates
must be treated as high-risk with a documented prior failure, and any test must
use our own purged/embargoed validation.

## 4. Carry / basis / perpetual funding

**FACT.** *Journal of Futures Markets* (2024, accepted) — Cao, Zhai & Luo,
"Anatomy of cryptocurrency perpetual futures returns": a cost-of-carry model, 134
return predictors (basis, momentum, volume, size, volatility); 48 significant;
a **basis + price-volume two-factor model explains all 48**.

**FACT.** "Fundamentals of Perpetual Futures" (arXiv `2212.06888`): perpetual
funding is typically paid **every 8 hours**; mean absolute futures–spot spread is
reported at ~60–100% per year across cryptocurrencies; carry strategies deliver
significant alpha vs the Liu–Tsyvinski–Wu 3-factor model.

**FACT.** "The Crypto Carry Trade" (Christin, Routledge, Soska, Zetlin-Jones),
cited in a 2026 CFTC comment letter: shorting perpetuals and holding spot earned
high realized returns; a BTC Tether-denominated carry trade is reported with an
annualized Sharpe of 8.76 (coin-denominated 4.93). The same letter stresses
**funding interpretation caveats and exchange-solvency risk (FTX)**.

**APPLICABILITY.** Carry/basis is the best-documented orthogonal crypto exposure
in the literature and is now **data-feasible here** (funding/mark/index downloaded
from perp listing). But reported Sharpes are extreme and depend on
arbitrage/margin/exchange assumptions; **exchange risk and funding costs mean it
must be tested as a standalone engine under our own cost model**, not assumed.

## 5. Machine learning / validation methods

**FACT.** López de Prado, M. (2018), *Advances in Financial Machine Learning*,
Wiley, ISBN `9781119482086`. Contributes: information-driven bars, the
**triple-barrier** labelling method, **meta-labelling** (a second model decides
whether to act on a primary model's side), sample weights for overlapping labels,
**fractionally differentiated features**, **purged K-fold CV with embargo**, and
combinatorial purged CV to reduce backtest overfitting.

**APPLICABILITY.** Provides the *methodology* our Validation Framework already
requires (purge + embargo). It is a methods source, **not** evidence that ML
improves returns. Meta-labelling matches our intended "second-stage filter"
architecture exactly.

## 6. Range-based volatility estimators

**FACT.** Parkinson (1980), *J. Business* 53:61–65; Garman & Klass (1980);
Rogers & Satchell (1991), *Ann. Appl. Probab.* 1:504–512; Yang & Zhang (2000),
*J. Business* 73:477–491.

**FACT (efficiency).** Range-based estimators are commonly reported as ~5–8× more
statistically efficient than close-to-close at equal sample size.

**FACT (complexity caveat — directly relevant).** *Empirical Economics* (2026),
"Is complexity always better? A model-free assessment of range-based volatility
estimators", DOI `10.1007/s00181-025-02873-3`: across G7 indices, **Garman–Klass
consistently outperforms**; **Yang–Zhang is generally the worst** despite being
the most complex; RS and YZ "do not provide significant predictive improvements".

**APPLICABILITY.** There is a documented efficiency gain, **but also documented
evidence that simpler estimators beat complex ones**. This supports testing ATR
vs (GK/PK) only, and argues against adopting YZ "because it is sophisticated".

---

## Summary implications (INTERPRETATION)

1. Trend following and crypto momentum have real academic support, but a
   well-known critique attributes much of TSMOM to volatility scaling — so our own
   tests must ablate signal vs sizing.
2. The most relevant prior crypto cross-sectional attempt on Binance perps
   **failed**; this must temper expectation and raise the validation bar.
3. Carry/basis is the strongest *orthogonal* candidate and is now data-feasible.
4. ML/validation methodology is available; ML's *value* is not assumed.
5. Simpler volatility estimators may beat complex ones — avoid complexity.

No source here validates any strategy for this project. All candidates remain
UNTESTED until our own pre-registered experiments run.
