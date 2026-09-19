# CELL-003 — Architecture / Next-Step Audit

| Field | Value |
|-------|-------|
| **Cell** | CELL-003 |
| **Status** | COMPLETED |
| **Audit date** | 2026-09-16 |
| **Branch** | `research/diagnostic-generalization` |
| **Basis** | Verified repository evidence only (committed results, specs, registry, decision log). No new strategy implemented. |
| **Production code touched** | No |

---

## 1. Established findings

1. **No strategy has passed.** P3-EXP-001/002/003 all FAIL; EXP-001…004 all FAIL
   or MIXED; F6 of `docs/PHASE_D_CRITICAL_EVALUATION.md` confirmed.
2. **Turtle (genuine futures) fails OOS in both directions.** P3-EXP-001: long
   arms test PF 0.813 / 0.852, short negative throughout.
3. **Costs are not the cause** (P3-EXP-002; EXP-002). Full-sample PF ≥ 1.0 to a
   0.35%/side stress for `long_raw`, but the volatility-scaled arm fails the
   preregistered stress threshold (1.037 < 1.05).
4. **Sizing dominates the headline.** Fixed notional beats volatility scaling on
   PF, drawdown and significance (P3-EXP-001 ablation); this is consistent with
   Kim/Tse/Wald (2016).
5. **The implemented carry proxy did not harvest funding.** P3-EXP-003 net funding
   PnL −11,306 USDT; positive full-sample PF is directional, not carry.
6. **Pullback long is not validated.** The 2025 edge failed fresh 2026 OOS
   (EXP-004 / DEC-006), and the 2025 result was concentrated in a few trades
   (PHASE 2 §9).
7. **Phase 2's supported explanations are regime shift and sampling/right-tail
   concentration**, with breakout follow-through, costs and data quality ruled
   out. Permanent decay is explicitly unproven.
8. **Data is now genuine** (`user_data/data_p3`: futures OHLCV + 1h mark +
   funding), resolving SI-1.

## 2. Weak / uncertain findings

- **Regime attribution.** 2026 had ~60% of development volatility and a bear
  tape; both holdouts are same-direction bear markets, so regime is confounded
  with time. PHASE 2 explicitly did not justify a filter.
- **Right-tail dependence.** Demonstrated for the consumed 2025 pullback result;
  for Turtle it is inferred, not directly tested on a clean window.
- **Carry.** The FAIL is about one naive single-leg, trailing-sign proxy, not carry
  in general (no spot hedge, no basis definition).
- **Cross-sectional momentum.** Academic crypto momentum exists, but the closest
  prior study on this exact venue/instrument class failed (Fayez Junior 2026).
- **`long_raw` full-sample significance (p=0.0020)** is a full-sample statistic on
  a non-pristine window, not an OOS pass.

## 3. Unsupported assumptions (must not drive work)

- That any component (momentum, carry, regime, ML, router) has incremental value
  here — zero components meet the "robust incremental OOS value" bar.
- That a regime/volatility filter would have made 2026 profitable (untested;
  prohibited in PHASE 2).
- That the volatility-scaled compounded headline is evidence of signal edge.
- That carry is refuted generally, or that residual momentum transfers from
  equities.

## 4. Missing experiments

| Slot | State | Note |
|------|-------|------|
| P3-EXP-004A cross-sectional momentum | not implemented | closest prior attempt failed (Fayez Junior 2026) |
| P3-EXP-004B residual momentum | not implemented | equity-only prior; look-ahead control required |
| P3-EXP-005 Turtle + momentum | not implemented | needs a validated component |
| P3-EXP-006 ATR vs Garman–Klass estimator | not implemented | low-complexity, preregistered |
| P3-EXP-007 regime | not implemented | PHASE 2 documented a shift but no filter |
| P3-EXP-008 ML meta-filter | not implemented | must be last, on a validated baseline |
| Walk-forward harness | **not implemented** | mandated by frozen spec §9; only a README exists |

## 5. Proposed next experiments (smallest high-information set, evidence-driven)

**N1 — Implement and run the frozen walk-forward validation harness (§9).**
*Why:* the binding methodological weakness is a single, non-pristine, ~20-month
test window. §9 already mandates anchored walk-forward; `research/walk_forward/`
documents the scheme but contains no code. Apply it to the two **already
implemented** engines (P3-EXP-001 long arms, P3-EXP-003) with parameters
unchanged. This adds information without adding a strategy.
*Evidence:* `docs/FROZEN_IMPLEMENTATION_SPEC.md` §9; `research/walk_forward/README.md`;
PHASE 2 §17 (under-powered single window).
*Caveat:* `walk_forward/README.md` says only A1–A8 passers enter. That rule
predates three failed genuine-futures experiments; measuring *why* failed setups
are unstable is exactly the gap. Recommend the rule be revisited explicitly
(governance note), not silently overridden.

**N2 — P3-EXP-006, ATR vs Garman–Klass as the sizing/stop input.**
*Why:* PHASE 2 attributed failure partly to volatility compression; the vol input
drives every stop and stake. A single pre-declared estimator comparison tests
whether the *input* (not direction) materially changes 2019–2026 behaviour.
*Evidence:* frozen spec §6.4; PHASE 2 §6; F11.
*Overfitting risk:* LOW — one pre-declared comparison, no search, YZ excluded.

**N3 — P3-EXP-007, regime states (volatility/efficiency terciles) applied to
selection / sizing / allocation, boundaries fixed on train/validation only.**
*Why:* it directly tests PHASE 2's most-supported explanation. Designed as a
falsification test (reject if it removes profitable trades or destabilises OOS).
*Evidence:* frozen spec §6.5; PHASE 2 §15–16.
*Overfitting risk:* HIGH — mitigated by fixing tercile boundaries causally and on
train/validation only, and by treating "no improvement" as the expected outcome.

**Explicitly deferred:** P3-EXP-004A (documented near-identical prior failure),
P3-EXP-005 (requires a validated component), P3-EXP-008 (ML must be last, on a
validated baseline — none exists). P3-EXP-004B is a *possible* second orthogonal
probe but is equity-only evidence and needs strict rolling-beta leakage controls.

## 6. Why each proposed experiment adds information

- **N1** converts "one window said X" into "k windows said X", which is the only
  way to separate a real edge from a regime/tail draw on a consumed holdout.
- **N2** isolates whether the measured failure is about *what is traded* (signal)
  or *how much/where the stop is* (volatility input) — a cheap, orthogonal cut.
- **N3** is the only proposal that can support or falsify the regime explanation
  PHASE 2 left open; a null result is itself high-information and prevents a
  regime filter from being added on superstition.

## 7. Risks of overfitting

- Regime/volatility work is the highest risk: tercile boundaries, lookbacks and
  application modes are all degrees of freedom. Contains: causal computation
  independent of outcomes, boundaries on train/validation only, one pre-declared
  variant per application, and no threshold tuned to 2026.
- Momentum/residual work risks factor/β look-ahead; must estimate betas only on
  data strictly before the ranking date (spec §6.3).
- Any walk-forward parameter selection risks re-introducing the search the frozen
  spec prohibits; the harness must choose parameters per the existing frozen
  values, not optimise them.
- The 2025/2026 reuse means any "improvement" fitted to those windows is void;
  only new data (post-2026-09) can provide a pristine check (SI-2).

## 8. Verification / evidence commands

```powershell
git log --oneline -10
python -m pytest tests -q                 # 133 passed
python -m ruff check .                    # clean
python -m ruff format --check .           # clean
```

**Post-wave reconciliation (final integrity pass).** The verification above is
this cell's own run. The final post-wave tree is **intentionally not clean**
(eight repaired research files plus `WAVE.md`/`SYNTHESIS.md` modified; the cell
reports untracked), but none of that touches the frozen production subtrees,
whose diff is **zero lines**. No Phase-3 experiment was executed by this cell or
the wave: N1/N2/N3 and P3-EXP-004A/004B/005/006/007/008 remain proposals only.

Evidence read in full: `docs/EXPERIMENT_REGISTRY.md`, `docs/FROZEN_IMPLEMENTATION_SPEC.md`,
`docs/EXTERNAL_EVIDENCE.md`, `docs/PHASE_D_CRITICAL_EVALUATION.md`,
`docs/ISSUES_LOG.md`, `research/preregistration/*`, `research/decisions/DECISION_LOG.md`,
`research/experiment_results/PHASE2_DIAGNOSTIC.md`, `EXP-001…004`, `P3-EXP-001…003`,
`research_lib/strategies/*`, `user_data/strategies/shared/pa_indicators.py`,
`research/walk_forward/README.md`.

## 9. Remaining blockers / residual risk

- SI-2 (no pristine holdout) is open and blocks any confirmatory claim.
- `docs/PHASE_D_CRITICAL_EVALUATION.md` and the "nine critical questions" predate
  P3 execution and are partly answered now (see addendum added to that document).
- No component is validated; adding one before N1/N2 would compound an
  unvalidated base.
- Governance tension: walk-forward README's A1–A8 gate vs the need to measure
  stability of failed methods — flagged, not silently changed.

## 10. OpenCode session ID

Not exposed by the execution environment in this session.
