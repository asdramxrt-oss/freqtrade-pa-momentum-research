# Decision log

Every decision that changes the research direction, the rules, or the status of a
strategy is recorded here. A decision is never edited after the fact; a changed
decision is a new entry that supersedes the old one.

| ID | Date | Type | Decision | Evidence |
|----|------|------|----------|----------|
| DEC-001 | 2026-09-16 | Governance | Research charter and experiment protocol frozen. Project established as a standalone repository, isolated from all pre-existing trading/research repositories. | `research/preregistration/research_charter.md`, `research/preregistration/experiment_protocol.md` |
| DEC-002 | 2026-09-16 | Strategy verdict | **EXP-001 (Turtle raw baseline) = FAIL.** 4 of 8 acceptance criteria passed. Failures: per-trade expectancy not significant (p=0.066), OOS 2025 negative (−18.98%, PF 0.80), wallet max drawdown 61.55%. | `research/experiment_results/EXP-001.md`, `EXP-001.json` |
| DEC-003 | 2026-09-16 | Strategy verdict | **EXP-002 (Turtle with realistic transaction costs) = FAIL.** 5 of 9 criteria passed (A1, A2, A7, A8, M1). Same failures as EXP-001: expectancy p=0.066, OOS 2025 −18.98% (PF 0.80), wallet max drawdown 61.55%. Cost is a real but non-binding constraint — profit factor stays above 1.00 until ~0.80% per side (1.61% round trip), so costs do not cause the failure. | `research/experiment_results/EXP-002.md`, `EXP-002.json`, `EXP-002.raw.json` |

Founding commit (foundation + EXP-001 implementation, on `main`):
`12acbf7017a04418dbfa54771edf5c97b358d618`
Experiment branch: `research/turtle-baseline` (same tree).

EXP-002 freeze commit (spec + config + cost-sweep tooling, on `research/turtle-costs`):
`8646616`
Baseline strategy logic unchanged at `12acbf7017a04418dbfa54771edf5c97b358d618`.
EXP-002 branch: `research/turtle-costs`.

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
