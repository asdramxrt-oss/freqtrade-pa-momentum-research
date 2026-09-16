# Hypothesis — Breakout-retest continuation

**Strategy family:** `user_data/strategies/breakout_retest/`
**Reference experiment:** EXP-005 (standalone), EXP-006 (combined with Turtle)
**Status:** PLANNED — must not be implemented before EXP-004 is recorded.

## 1. Hypothesis

> A breakout that is retested and holds turns a former resistance level into
> support, and entries taken after the retest holds have a better risk/reward
> than entries taken at the breakout itself.

## 2. Market intuition

The retest is a liquidity event: the level that trapped breakout sellers is
revisited, absorbed, and then defended. If the level holds, the pool of sellers
above it is smaller than it was at the original breakout.

## 3. State machine (must be explicit in code)

The implementation must distinguish four states and must not collapse them:

| State | Definition |
|-------|-----------|
| `BREAKOUT` | close exceeds a level that had previously rejected price |
| `RETEST` | price returns to within a tolerance band around that level |
| `FAILED_RETEST` | price closes through the level against the breakout direction |
| `CONTINUATION` | price closes back in the breakout direction after a held retest |

Each state transition is evaluated on closed candles only.

## 4. Exact entry

Long entry on the `CONTINUATION` transition after a `RETEST` that never entered
`FAILED_RETEST`.

Level definition, tolerance band, and the maximum number of bars allowed between
breakout and retest are fixed in `research/experiment_specs/EXP-005.md` before
implementation.

## 5. Exact exit

Baseline intent: identical exit and stop to Turtle, so the comparison isolates
the entry mechanism.

## 6. Risk management

Identical to the baseline: 1% risk at a fixed 2 × ATR stop from entry.

## 7. Parameters

To be fixed in EXP-005 before the run and recorded with the result.

## 8. Expected failure modes

| Mode | Why |
|------|-----|
| Level definition is arbitrary | "Former resistance" is easy to define loosely and then overfit |
| No retest occurs | Strong trends simply leave; trade count collapses |
| Retest tolerance is the whole game | A wide band manufactures setups, a tight band manufactures none |
| Look-ahead in state machine | A retest is only complete once it is over — a partial current-bar retest must not be treated as held |
| Duplication of Turtle | Retest entries may simply be late Turtle entries |

## 9. ML hypothesis (later, EXP-012)

Given a valid retest, estimate the probability that the retest holds and
continuation follows. Second-stage filter only.

## 10. Validation and rejection

Charter thresholds A1–A8, plus the complementarity test in EXP-006. A retest
strategy whose trades overlap almost entirely with Turtle's is rejected as
duplication.
