# Hypothesis — Turtle / Donchian absolute trend momentum

**Strategy family:** `user_data/strategies/turtle/`
**Reference experiment:** EXP-001
**Reference baseline:** this IS the reference baseline.

## 1. Hypothesis

> Persistent directional price moves in liquid crypto assets begin with a price
> breaking out of its recent range, and a trailing channel exit captures enough
> of the subsequent move to more than pay for the false breakouts.

This is the classic Turtle premise stated so that it can be falsified: if the
premise is true, a small number of large winners must outweigh a large number of
small losers, and the advantage must survive realistic trading costs.

## 2. Market intuition

A Donchian breakout is the most primitive possible definition of "price is going
somewhere it has not been recently". It requires no forecast, no valuation view
and no indicator fitting. If trend persistence exists at all, this is the
cheapest way to express it, which makes it the correct yardstick for every more
elaborate idea in this programme.

## 3. Exact entry

Long entry when, on a closed 4h candle:

```
close[t] > max(high[t-20 : t])
```

The channel **excludes the current bar** (one-bar shift) so the comparison is
against prior price only. The signal is taken only on the **rising edge** of the
breakout condition, so one breakout episode yields exactly one entry. Entries
are additionally suppressed while ATR(20) is undefined.

## 4. Exact exit

Any of:

1. Channel exit — `close[t] < min(low[t-10 : t])`.
2. Fixed ATR stop — `entry_price - 2 * ATR(20 at entry)`, evaluated intrabar by
   `custom_stoploss`.
3. Hard backstop — −30%, used only if the ATR lookup fails.

Profit targets are deliberately absent: an ROI target would truncate the right
tail that this entire hypothesis depends on.

## 5. Risk management

- Stop distance is `2 × ATR(20)` measured at entry and does not trail.
- The ATR used is the value from the last analysed candle at or before the entry
  timestamp, cached on the trade. Nothing about the future enters the stop.
- Position size risks 1% of equity across that stop distance, capped at the full
  account value.
- Long only, spot, no leverage, no pyramiding, max 5 concurrent trades.

## 6. Parameters

| Parameter | Value | Tunable? |
|-----------|-------|----------|
| `entry_period` | 20 | No — classic Turtle value, fixed by spec |
| `exit_period` | 10 | No — classic Turtle value, fixed by spec |
| `atr_period` | 20 | No |
| `atr_stop_multiple` | 2.0 | No |
| `risk_per_trade` | 0.01 | No |
| `timeframe` | 4h | No |

These are fixed precisely so that a later improvement cannot be attributed to
parameter archaeology. Parameter sensitivity is studied as its own experiment.

## 7. Expected failure modes

| Mode | Why it is expected |
|------|-------------------|
| Whipsaw in range-bound regimes | Most breakouts fail; the stop is taken repeatedly |
| Long crypto bear markets | Long-only spot cannot profit from persistent downtrends (2022, 2025) |
| Cost sensitivity | ~2 round trips per trade means fees scale with turnover |
| Deep drawdowns | Trend systems give back a large share of open profit before the channel exit |
| Regime dependence | Profit concentrated in strong trending years (2020–2021) |
| Small-sample luck | With 4h crypto data, trade counts can look large while the effective number of *independent* trend episodes is far smaller |

## 8. ML hypothesis (later, EXP-010)

Given a breakout that already satisfies the rule-based setup, predict the
probability that the move continues far enough to cover costs. The model is a
second-stage filter over an existing setup, never an independent trade
generator. It must be trained strictly chronologically and may not use the OOS
holdout for threshold selection.

## 9. Validation method

Per `research/preregistration/experiment_protocol.md`:

1. Full-sample run at fee 0.05%.
2. Per-year run for every calendar year.
3. OOS holdout 2025 (evaluated once per strategy version).
4. Cost sensitivity at fee 0.10% and 0.20%.
5. Parameter sensitivity (entry/exit period, ATR multiple) as a separate
   pre-registered experiment.
6. Pair-level breakdown.
7. Monte Carlo / trade-order reshuffling.
8. Walk-forward when the above survive.

## 10. Rejection criteria

Rejected as an edge if any charter criterion A1–A8 fails, specifically:

- fewer than 200 trades in the full sample,
- profit factor < 1.10 at base cost, or < 1.05 at stress cost,
- per-trade expectancy p-value >= 0.05,
- negative OOS return or OOS profit factor < 1.00,
- wallet max drawdown >= 35%,
- profitable in fewer than 60% of calendar years.

A rejection means "not evidence of an edge", not "worthless idea". The strategy
is retained as the reference baseline regardless of its own verdict.
