# Decision log

Every decision that changes the research direction, the rules, or the status of a
strategy is recorded here. A decision is never edited after the fact; a changed
decision is a new entry that supersedes the old one.

| ID | Date | Type | Decision | Evidence |
|----|------|------|----------|----------|
| DEC-001 | 2026-09-16 | Governance | Research charter and experiment protocol frozen. Project established as a standalone repository, isolated from all pre-existing trading/research repositories. | `research/preregistration/research_charter.md`, `research/preregistration/experiment_protocol.md` |
| DEC-002 | 2026-09-16 | Strategy verdict | **EXP-001 (Turtle raw baseline) = FAIL.** 4 of 8 acceptance criteria passed. Failures: per-trade expectancy not significant (p=0.066), OOS 2025 negative (−18.98%, PF 0.80), wallet max drawdown 61.55%. | `research/experiment_results/EXP-001.md`, `EXP-001.json` |
| DEC-003 | 2026-09-16 | Strategy verdict | **EXP-002 (Turtle with realistic transaction costs) = FAIL.** 5 of 9 criteria passed (A1, A2, A7, A8, M1). Same failures as EXP-001: expectancy p=0.066, OOS 2025 −18.98% (PF 0.80), wallet max drawdown 61.55%. Cost is a real but non-binding constraint — profit factor stays above 1.00 until ~0.80% per side (1.61% round trip), so costs do not cause the failure. | `research/experiment_results/EXP-002.md`, `EXP-002.json`, `EXP-002.raw.json` |
| DEC-004 | 2026-09-16 | Strategy verdict | **EXP-003 (Pullback continuation) = MIXED / REQUIRES FURTHER VALIDATION.** Combined object fails A1–A8 (4/8: A3, A4, A5, A6), caused entirely by the short side (PF 0.73, −55.95%, DD 61.73%, 9/10 pairs negative, expectancy significantly negative). Long-only passes all 8 (PF 1.567, DD 24.4%, OOS +14.01%, 6/7 years, all 10 pairs profitable) but is a pre-registered variant on a single holdout — promising, not validated. Short side rejected. Geometry does not separate winners from losers. | `research/experiment_results/EXP-003.md`, `EXP-003.json`, `EXP-003.raw.json` |
| DEC-005 | 2026-09-16 | Governance | **EXP-004 slot re-scoped.** The frozen charter sequence listed EXP-004 as "Turtle + Pullback". At the research owner's explicit direction the EXP-004 slot is instead a **fresh out-of-sample validation of the frozen long-only pullback strategy** (`c4bee8e`), with combination research explicitly prohibited for this slot. The charter sequence and this experiment are therefore reconciled by record, not by silent divergence. Turtle+Pullback is deferred and not authorised. | `research/experiment_specs/EXP-004.md` |
| DEC-006 | 2026-09-16 | Strategy verdict | **EXP-004 (frozen long pullback, fresh OOS) = FAILS FRESH OOS.** On the previously unevaluated window 2026-01-01 → 2026-09-16 the frozen strategy produced 64 trades, PF 0.607, net −12.75%, 25% win rate, expectancy −19.93 USDT (p = 0.164), wallet DD 21.70%. Only A6 passed; A1, A2, A3, A4, A5, A7 failed (A8 N/A). The EXP-003 long-only result did **not** replicate. No tuning, no pair removal, no parameter change, no combination. | `research/experiment_results/EXP-004.md`, `EXP-004.json`, `EXP-004.raw.json` |

Founding commit (foundation + EXP-001 implementation, on `main`):
`12acbf7017a04418dbfa54771edf5c97b358d618`
Experiment branch: `research/turtle-baseline` (same tree).

EXP-002 freeze commit (spec + config + cost-sweep tooling, on `research/turtle-costs`):
`8646616af81d7fae2ef0ae18d2eab25ca0468f78`
Baseline strategy logic unchanged at `12acbf7017a04418dbfa54771edf5c97b358d618`.
EXP-002 branch: `research/turtle-costs`.
EXP-002 results commit (results + DEC-003 + map):
`2fdcc8f4acd25593dd37337e9cbe3b2abdcd5b3a`

EXP-003 freeze commit (spec + configs, on `research/pullback-continuation`):
`a07e966eba904192fa51c29b2e8d9512358624b8`
EXP-003 implementation commit (strategy, shared primitives, tests):
`c4bee8e264a111aa2e72dbce203bd49db1484d8b`
EXP-003 results commit (results + DEC-004 + map):
`552fd763b08971f302cbc73f035115cc2a86813a`
Baseline strategy logic unchanged at `12acbf7017a04418dbfa54771edf5c97b358d618`.

EXP-004 pre-registration commit (spec + DEC-005, on `research/frozen-pullback-oos`):
`1a8e5ab29079319642e08fca78e6d2ed003f983d`
EXP-004 frozen strategy commit (unchanged from EXP-003 implementation):
`c4bee8e264a111aa2e72dbce203bd49db1484d8b`
EXP-004 results commit (results + DEC-006 + map):
`f17572d39f7e8f6fab73262ad5f770de93629017`

---

## DEC-002 — detail

**Decision.** The raw Turtle/Donchian baseline is not evidence of a deployable
edge. It is retained unchanged as the reference baseline and must not be
"improved" by tuning its periods or adding filters.

**Reasoning.**

1. Per-trade mean profit is not statistically distinguishable from zero at the
   5% level (p = 0.0658 over 1,347 trades). A large positive compounded return
   driven by a small number of winners is consistent with luck.
2. The untouched 2025 holdout lost 18.98% with a profit factor of 0.80. Beating a
   falling market is a defensive observation, not an edge.
3. Wallet-level maximum drawdown of 61.55% is far outside acceptable limits for
   any strategy that would hold real capital.
4. Tripling costs (0.05% → 0.20% per side) removed ~57% of compounded return and
   pushed drawdown to 71.18%, so the result is cost-sensitive.

**What was explicitly NOT done.**

- No parameter tuning to rescue the result.
- No indicators added.
- No re-run of the OOS window with different settings. One OOS evaluation was
  used and recorded.

**Consequences.**

1. The baseline stays frozen as the comparison yardstick (charter §5).
2. Next experiment: **EXP-002** — Turtle with realistic transaction costs, to
   complete the cost analysis (0.10% level, per-year cost runs, explicit fee and
   turnover totals) and to test slippage-assumption sensitivity.
3. EXP-010 onward (ML) now has a quantified target: lift per-trade expectancy
   significance and cut drawdown relative to the numbers in EXP-001.
4. Any future strategy must be compared against EXP-001's per-trade statistics,
   not against its compounded return.

**Open questions carried forward.**

- Would a volatility-scaled or regime-aware sizing scheme reduce drawdown without
  changing the entry mechanism? (Belongs to a sizing experiment, not to the
  baseline.)
- Is the 2020–2021 profit concentration a property of the market or of the
  strategy? (Requires cross-regime testing, not tuning.)

---

## DEC-003 — detail

**Decision.** The Turtle baseline is not rescued by cost analysis. Measured
across a six-point fee sweep (0.05% → 1.00% per side) with the strategy logic
frozen, it fails the same four acceptance criteria as EXP-001 (A3 significance,
A4 OOS return, A5 OOS profit factor, A6 drawdown). Costs are a real drag but are
**not** what makes the strategy fail. The baseline stays frozen.

**Evidence.**

| Fee/side | Profit factor | Net return | Wallet max DD | Fees | Fees % of gross profit |
|----------|---------------|------------|---------------|------|------------------------|
| 0.05% | 1.228 | +4,817.29% | 61.55% | 82,269 | 14.6% |
| 0.10% | 1.197 | +3,638.73% | 65.07% | 138,340 | 27.6% |
| 0.20% | 1.145 | +2,067.47% | 71.18% | 198,701 | 49.0% |
| 0.30% | 1.103 | +1,151.36% | 76.23% | 217,063 | 65.3% |
| 0.50% | 1.044 | +306.54% | 85.42% | 201,248 | 86.8% |
| 1.00% | 0.972 | −72.82% | 97.69% | 116,675 | 106.7% |

Breakeven: profit factor = 1.00 at 0.804% per side (1.61% round trip); net
return = 0 at 0.904% per side (1.81% round trip). Base and stress runs reproduce
EXP-001 to the decimal, and per-year base runs reproduce EXP-001 for all seven
years.

**Reasoning.**

1. All cost-specific criteria pass: A2 (PF ≥ 1.10 at 0.05%), A8 (PF ≥ 1.05 at
   0.20%) and M1 (PF ≥ 1.10 at 0.10%). Cost alone would not reject the strategy.
2. The edge survives to roughly 4× the realistic stress assumption before
   profit factor falls below 1.00, so the slippage assumption is not the weak
   point — the A3/A4/A5/A6 failures are.
3. Fees are nonetheless material: 14.6% of gross profit at base, 49.0% at
   stress, >100% at 1.00%. Any future strategy targeting this universe must
   account for the same magnitude of drag.
4. The same structural weaknesses persist: per-trade expectancy not significant,
   a negative untouched holdout, and a 61.55% wallet drawdown.

**What was explicitly NOT done.**

- No strategy-logic change, no filter, no indicator, and no parameter tuning.
- No re-run of the OOS window under changed settings. The 0.05%/0.10%/0.20%
  holdout runs are non-selection cost views of the EXP-001 strategy version; the
  only selection-relevant OOS evaluation remains EXP-001's.
- No baseline "improvement" to make the cost numbers look better.

**Consequences.**

1. Baseline remains frozen as the comparison yardstick.
2. EXP-003 (Pullback continuation standalone) is **not** started automatically.
   The frozen sequence requires an explicit decision before the next experiment.
3. The ML programme (EXP-010) keeps its quantified target: improve per-trade
   expectancy significance and reduce drawdown relative to EXP-001/EXP-002,
   while staying inside the cost envelope demonstrated here.

**Open questions carried forward.**

- Which failure is most tractable first: expectancy significance, OOS stability,
  or drawdown? (This decides the next experiment, and is a deliberate decision,
  not an automatic one.)
- Do the three losing pairs (ADA, DOT, LINK) share a property that a universe
  rule could have excluded *ex ante*, without overfitting? (Universe selection is
  itself an experiment.)
- Can a later strategy do better than the baseline **net of fees**, or only
  better gross? (Cost drag must be part of the acceptance test, not an
  afterthought.)

---

## DEC-004 — detail

**Decision.** The pullback-continuation hypothesis is **MIXED**: the pre-registered
combined strategy fails the acceptance framework, entirely because of the short
side, while the long side independently clears all eight criteria. The short
continuation setup is rejected. The long setup is promising but is **not**
validated and is **not** production-ready.

**Evidence (full sample 2019–2026, fee 0.05%).**

| Variant | Trades | PF | Net return | p-value | Wallet max DD | OOS 2025 | Profitable years | A1–A8 |
|---------|--------|----|------------|---------|---------------|----------|------------------|-------|
| Combined (primary) | 1,148 | 1.149 | +209.49% | 0.2366 | 36.39% | −3.57% (PF 0.95) | 5/7 | 4/8 FAIL |
| Long-only | 607 | 1.567 | +718.62% | 0.0112 | 24.43% | +14.01% (PF 1.34) | 6/7 | 8/8 PASS |
| Short-only | 641 | 0.728 | −55.95% | 0.0049 | 61.73% | +3.03% (PF 1.07) | 1/7 | 4/8 FAIL |

The combined failure set is A3 (expectancy not significant, p = 0.237), A4 (OOS
−3.57%), A5 (OOS PF 0.953) and A6 (drawdown 36.39%). The long side is profitable
in all 10 pairs; the short side is negative in 9 of 10. Trade-level MAE/MFE and
all geometry statistics (impulse size, pullback depth, duration, distance from
structure, trigger margin) are **almost identical for winners and losers**, so no
structural variable measured here explains success.

**Reasoning.**

1. The pre-registered primary object is the combined strategy, and it fails.
   Reporting only the long side would be retrospectively redefining the strategy.
2. The short side is not marginal: PF 0.73, −55.95%, 61.73% drawdown, expectancy
   significantly *negative* (p = 0.0049), 1/7 profitable years. It is rejected.
3. The long side passes every criterion with margin — including the ones the
   Turtle baseline could never clear (expectancy significance, OOS return,
   drawdown). That is the strongest lead in the programme so far.
4. But the long side is a pre-registered *variant*, evaluated on a single holdout,
   with an edge that is not explained by any measured geometry. Calling it
   validated or robust would overstate the evidence.

**What was explicitly NOT done.**

- No parameter tuning, no geometry filter fitted after the fact, no criterion
  changed after seeing results.
- The short side was **not** disabled to make the combined result look better.
- No combination with the baseline was built (that is EXP-004, not authorised).
- OOS was evaluated once per variant and not reused for selection.

**Consequences.**

1. Combined pullback continuation is not promoted and not combined with anything.
2. Short-continuation geometry is recorded as rejected for this universe.
3. EXP-004 is **not** started automatically; the next experiment requires an
   explicit decision.
4. The long-only pullback setup is the leading candidate for the next
   authorisation, and any follow-up must pre-register its own OOS protocol
   because this holdout has now been used.

**Open questions carried forward.**

- Is the long-only pullback edge stable under a **new** out-of-sample window, or
  was 2025 an accident? (Requires a future holdout, not a re-run of 2025.)
- Why is the short side structurally negative while the long side works? Is it
  the crypto long bias (a rising sample) rather than the geometry?
- Can position sizing or a portfolio rule extract the long edge without the
  combined-slot competition that made the combined run worse than its own long
  side?

---

## DEC-005 — detail

**Decision.** The EXP-004 slot is used for a **fresh out-of-sample validation of
the frozen long-only pullback continuation strategy**, not for the
`Turtle + Pullback` combination experiment named in the charter's pre-registered
sequence.

**Reasoning.**

1. EXP-003 left exactly one open lead: the long-only pullback variant (8/8
   criteria on the development sample, 2025 OOS +14.01%). The single most useful
   next step is to test whether that lead survives a period nobody has looked at,
   before spending effort on combination research that the earlier evidence does
   not yet justify.
2. The research owner directed this re-scope explicitly and prohibited any
   baseline combination in this slot.
3. The charter requires that a change to the frozen plan be recorded rather than
   made silently; this record supplies that.

**Consequences.**

1. EXP-004 = fresh OOS validation of `PullbackContinuationLong` at its frozen
   commit `c4bee8e`.
2. `Turtle + Pullback` is deferred; no combination is built or authorised.
3. The charter sequence table is now knowingly divergent for the EXP-004 row and
   is superseded by this decision for that row only.
4. EXP-005 and later remain unauthorised.

**Note.** This is a governance decision, not a strategy verdict; the EXP-004
verdict is recorded separately after the fresh run.

---

## DEC-006 — detail

**Decision.** The frozen EXP-003 long-only pullback-continuation strategy
**FAILS FRESH OOS**. The promising 2025 result did not replicate on a genuinely
unseen window.

**Evidence (fresh window 2026-01-01 → 2026-09-16, fee 0.05%, 10 pairs).**

| Metric | Value |
|--------|-------|
| Trades | 64 |
| Profit factor | 0.607 |
| Net return | −12.75% |
| Expectancy (USDT/trade) | −19.93 |
| Expectancy p-value | 0.1643 |
| Win rate | 25.0% (16 W / 48 L) |
| Wallet max drawdown | 21.70% |
| Market change (buy & hold) | −27.48% |

Criteria: A1 FAIL, A2 FAIL, A3 FAIL, A4 FAIL, A5 FAIL, A6 PASS, A7 FAIL, A8 N/A.
Only 1 of 7 evaluable criteria passed. The pre-registered rule classifies this as
FAIL because net return < 0 (A4) and profit factor < 1.00 (A5).

**Reasoning.**

1. The prior result was a single holdout (2025) on a strategy chosen from the
   development sample. On a fresh window it was net-negative with PF well below
   1. Even a defensive read (it lost less than a −27.5% market) is not an edge.
2. The negative point estimate is not itself statistically significant
   (p = 0.164; 64 trades), so the honest statement is "no evidence of a positive
   edge on fresh data", not "a proven losing system". The frozen rule uses
   absolute thresholds, not significance, for A4/A5, hence FAIL rather than
   INCONCLUSIVE.
3. The result is preserved as found. A poor fresh result is a legitimate research
   outcome.

**What was explicitly NOT done.**

- No parameter tuning, no pair removal/addition, no threshold change, no ML, no
  baseline combination.
- The OOS window was fixed before the run and not extended or altered afterwards.
- The strategy was run in exactly one configuration.

**Consequences.**

1. The long-only pullback hypothesis is **not validated**; EXP-003's 2025 result
   is recorded as non-replicating.
2. `Turtle + Long Pullback` (the charter's original EXP-004) is **not**
   authorised: there is no validated component to combine.
3. EXP-005 is **not** started; the programme stops pending an explicit decision.
4. Any future work on the pullback family must first explain why the 2026 window
   behaved differently, rather than re-fitting to it.

**Open questions carried forward.**

- Was 2025 a genuine but regime-specific effect, or noise? The 2026 window cannot
  distinguish these on its own.
- Does the pattern generalise to non-crypto or to a longer post-2026 sample once
  more data exists? (Requires waiting for data, not re-testing this window.)
- The Turtle and Pullback families have now both failed fresh evaluation; the
  programme's next step should be an explicit strategy-selection decision, not an
  automatic continuation.

---

## PHASE 2 — diagnostic reference (no strategy decision)

A diagnostic-only investigation of generalization failure is recorded in
`research/experiment_results/PHASE2_DIAGNOSTIC.md` (specification
`research/experiment_specs/PHASE2_DIAGNOSTIC.md`, branch
`research/diagnostic-generalization`). It changes no strategy, adds no filter and
reaches **no strategy verdict**.

Outcome: **multiple plausible explanations** — sampling variation /
trade-concentration and a market-regime shift (volatility compression plus a
long-only bear holdout) — with breakout follow-through, transaction costs and
data quality ruled out as primary causes, and permanent strategy decay recorded
as **unproven**. No strategy is validated by this phase.
