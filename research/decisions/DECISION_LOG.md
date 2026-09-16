# Decision log

Every decision that changes the research direction, the rules, or the status of a
strategy is recorded here. A decision is never edited after the fact; a changed
decision is a new entry that supersedes the old one.

| ID | Date | Type | Decision | Evidence |
|----|------|------|----------|----------|
| DEC-001 | 2026-09-16 | Governance | Research charter and experiment protocol frozen. Project established as a standalone repository, isolated from all pre-existing trading/research repositories. | `research/preregistration/research_charter.md`, `research/preregistration/experiment_protocol.md` |
| DEC-002 | 2026-09-16 | Strategy verdict | **EXP-001 (Turtle raw baseline) = FAIL.** 4 of 8 acceptance criteria passed. Failures: per-trade expectancy not significant (p=0.066), OOS 2025 negative (−18.98%, PF 0.80), wallet max drawdown 61.55%. | `research/experiment_results/EXP-001.md`, `EXP-001.json` |

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
