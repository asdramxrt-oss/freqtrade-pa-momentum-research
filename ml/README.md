# ML layer (EXP-010 → EXP-013)

Nothing in this directory is implemented yet, and that is deliberate.

## Hard constraints from the charter

1. **No ML before the matching rule-based setup is tested and recorded.** ML on
   Turtle (EXP-010) cannot begin until EXP-002 is decided; ML on Pullback
   (EXP-011) cannot begin until EXP-004 is decided; and so on.
2. **ML is a second-stage filter, never a trade generator.**

   ```
   PRICE -> RULE-BASED SETUP -> FEATURE ENGINE -> SPECIALISED MODEL -> SCORE -> RISK -> EXECUTION
   ```

   A model may only score setups that already satisfy the rule-based definition.
   Manufacturing trades outside the setup would be a different architecture and
   would require its own explicit hypothesis.
3. **One prediction problem per strategy.** There is no global buy/sell model.

| Directory | Prediction problem |
|-----------|-------------------|
| `turtle/` | Given a valid Donchian breakout, probability of meaningful trend continuation |
| `pullback/` | Given a valid pullback setup, probability of successful continuation |
| `breakout_retest/` | Given a valid retest, probability that the retest holds and continuation follows |
| `volatility_expansion/` | Given valid compression + expansion, probability of sustained directional continuation |
| `features/` | Shared, causal feature construction |
| `labels/` | Label definitions and horizons |
| `validation/` | Chronological splits, walk-forward, leakage checks |

## Data hygiene rules

- Features must be available at the actual decision time. If a feature needs a
  confirmed swing, the confirmation lag is part of the feature.
- Labels may use later information, but only information that would genuinely
  have become available later — and the label horizon must be recorded.
- Splits are strictly chronological. No shuffling, ever.
- Validation is walk-forward, not a single holdout.
- Threshold selection may not use the evaluation period.
- Every run records feature definitions, label definition, label horizon,
  training / validation / test periods, model parameters, random seed and model
  version.
- Model binaries are git-ignored (`ml/**/*.pkl`, `*.joblib`, `*.onnx`); the
  recipe that produces them is what gets committed.

## Success definition

ML is not required to produce a higher return. It is required to improve
**per-trade expectancy significance** and/or **drawdown** relative to the
rule-based baseline, measured on data it has not seen, at realistic costs.
Failing that, it is recorded as a negative result like everything else.
