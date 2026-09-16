# Hypothesis — Pullback continuation

**Strategy family:** `user_data/strategies/pullback/`
**Reference experiment:** EXP-003 (standalone), EXP-004 (combined with Turtle)
**Status:** PLANNED — must not be implemented before EXP-002 is recorded.

## 1. Hypothesis

> After an impulse move establishes trend, a controlled pullback that holds the
> prior structure and then resumes provides a better entry price and a better
> risk/reward than chasing the original breakout.

Turtle buys the breakout itself. This hypothesis claims the *second* entry — the
retracement — is cheaper and more selective. The two can only be complements if
the trades and return streams actually differ.

## 2. Market intuition

Breakouts attract late momentum buyers and resting liquidity; both push price
back toward the breakout level. Trend followers who require continuation
confirmation after the pullback buy a smaller stop distance for a similar
continuation probability.

## 3. Structural definition (not a moving-average crossover)

The setup must be expressed in price-structure terms:

1. **Impulse** — a directional leg whose size and speed are large relative to
   recent ATR (e.g. leg range > k × ATR over a small number of bars).
2. **Pullback depth** — retracement of the impulse leg measured in ATR units,
   not in percent, and bounded above and below (too shallow = no opportunity,
   too deep = structure broken).
3. **Structure intact** — the pullback must not violate the swing low that
   defined the impulse origin.
4. **Distance from impulse** — how far price has travelled from the impulse high.
5. **Candle structure** — contraction of candle ranges during the pullback
   (selling pressure fading).
6. **Continuation confirmation** — a bar closing back in the impulse direction
   through the pullback's own short-term high, or through a defined level.

## 4. Exact entry

To be fixed in `research/experiment_specs/EXP-003.md` before implementation, in
terms of the six structural measurements above with explicit numeric bounds.
Causality requirement: every swing used must be confirmed by the time of the
decision bar; no future pivot may be referenced.

## 5. Exact exit

Initial specification intent: the same channel exit as Turtle, plus the same
2 × ATR stop, so that the comparison isolates the *entry*, not the exit. Any
deviation must be pre-registered.

## 6. Risk management

Same as the baseline: 1% risk at a fixed 2 × ATR stop, long only, max 5
positions, no pyramiding.

## 7. Parameters

To be specified in EXP-003. Must be recorded with defaults before the run.

## 8. Expected failure modes

| Mode | Why |
|------|-----|
| Pullback never confirms | Trend leaves without the retracement |
| Pullback becomes reversal | Structure break misclassified as a pullback |
| Look-ahead via pivots | Swing points are only knowable with a delay — the single most likely leakage source here |
| High correlation with Turtle | If entries cluster in the same moves, the "complement" is a duplicate |
| Parameter fragility | Depth bounds are the obvious overfitting surface |

## 9. ML hypothesis (later, EXP-011)

Given a pullback that satisfies the structural setup, estimate the probability of
a successful continuation. Second-stage filter only.

## 10. Validation and rejection

Same protocol and thresholds as the charter (A1–A8). Additionally, EXP-004 must
demonstrate complementarity, not just higher combined profit:
signal overlap, trade overlap, return correlation and drawdown correlation
against Turtle. If overlap is near-total, the combination is rejected as
duplication even if the combined equity curve looks better.
