# Hypothesis — Volatility compression → expansion

**Strategy family:** `user_data/strategies/volatility_expansion/`
**Reference experiment:** EXP-007 (standalone), EXP-008 (combined with Turtle)
**Status:** PLANNED — must not be implemented before EXP-006 is recorded.

## 1. Hypothesis

> Breakouts that emerge from an unusually compressed volatility state behave
> differently from ordinary breakouts, because the expansion of range is itself
> information about the balance of supply and demand.

This is not a restatement of Turtle. Turtle measures *where* price is relative to
its range. This hypothesis measures *how compressed the range was* before the
break. The two can be orthogonal: a breakout can occur from a wide, already-
expanded range (ordinary Turtle) or from a historically tight coil (this idea).

## 2. Market intuition

Compression represents agreement and stored energy. Expansion out of
compression represents a resolution of that agreement, which is more likely to
be followed by a directional move than a breakout that occurs after volatility
has already expanded.

## 3. Measurable inputs to research

All must be causal and expressed as scale-free (normalised) quantities where
possible:

| Input | Description |
|-------|-------------|
| ATR percentile | ATR(20) ranked against its own trailing history |
| Realised volatility | std-dev of log returns over a rolling window, ranked |
| Range compression | ratio of recent N-bar range to a longer M-bar range |
| Candle-range contraction | mean candle range now vs trailing distribution |
| Local range width | Donchian width over a short window, normalised by midpoint |
| Donchian width ratio | short-window width / long-window width |
| Inside-bar behaviour | consecutive inside bars, NR7-style narrowing |
| Range expansion | current range vs compressed baseline |

## 4. Exact entry

To be fixed in `research/experiment_specs/EXP-007.md` before implementation:
a compression condition combined with a directional expansion condition.

## 5. Exact exit

Baseline intent: identical exit and stop to Turtle, so the comparison isolates
the entry condition.

## 6. Risk management

Identical to the baseline: 1% risk at a fixed 2 × ATR stop from entry.

## 7. Parameters

To be fixed in EXP-007 and recorded with the result.

## 8. Expected failure modes

| Mode | Why |
|------|-----|
| Compression is common, expansion is not | The filter may remove far too few trades to matter |
| Compression precedes both directions | Symmetric setup, long-only implementation throws away half the signal |
| Percentile windows are a tuning surface | Easy to overfit the lookback that defines "unusual" |
| Overlap with Turtle | If compression almost always precedes a 20-bar breakout, the filter is decorative |
| Regime sensitivity | Crypto volatility regimes are long-lived; a percentile threshold fitted to one era may fail in another |

## 9. ML hypothesis (later, EXP-013)

Given valid compression followed by expansion, estimate the probability of
sustained directional continuation. Second-stage filter only.

## 10. Validation and rejection

Charter thresholds A1–A8. Additionally, EXP-008 must show that the compression
filter changes *which* trades are taken, not merely how many — an entropy / trade
overlap comparison against Turtle is required. If the filtered trade set is a
near-subset of Turtle's with no change in per-trade expectancy, the hypothesis is
rejected as decorative.
