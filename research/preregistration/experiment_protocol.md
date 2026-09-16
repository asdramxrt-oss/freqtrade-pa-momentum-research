# Experiment protocol — frozen baseline conditions

**Status:** FROZEN
**Frozen on:** 2026-09-16

Every experiment that is compared against the Turtle baseline uses the
conditions below unless its specification states a deviation *before* it is run.
Deviations are recorded in both the specification and the result.

---

## Market universe

| Item | Value |
|------|-------|
| Exchange | Binance (spot) |
| Quote currency | USDT |
| Timeframe | 4h |
| Pairs (10) | BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, XRP/USDT, ADA/USDT, DOGE/USDT, LINK/USDT, AVAX/USDT, DOT/USDT |
| Pairlist method | `StaticPairList` (explicit whitelist, no dynamic filtering) |
| Candle type | spot |
| Data source | `freqtrade download-data` from Binance public endpoints |
| Data on disk (measured 2026-09-16) | BTC/ETH from 2019-01-01; BNB/XRP/ADA/LINK from 2019-01-01; DOGE from 2019-07-05; DOT/SOL from 2020-08; AVAX from 2020-09 |
| Raw data in Git | never (git-ignored, reproducible via `user_data/scripts/download_data.ps1`) |

## Periods

| Segment | Range | Purpose |
|---------|-------|---------|
| Full sample | 2019-01-01 → 2026-01-01 | Headline metrics |
| Per-year | each calendar year | Year-level robustness |
| OOS holdout | 2025-01-01 → 2026-01-01 | Final untouched evaluation, one evaluation per strategy version |
| Walk-forward | `research/walk_forward/` | Added when a strategy passes preliminary checks |

The OOS holdout is evaluated **once per strategy version**. The number of
evaluations is recorded in the experiment result.

## Cost assumptions

Freqtrade backtesting models transaction costs through the configured fee. There
is no native slippage model, so slippage is handled as an explicit *cost
sensitivity sweep* rather than a single estimate.

| Scenario | Fee assumption | Interpretation |
|----------|---------------|----------------|
| Base | 0.05% per side | Optimistic taker fee |
| Mid | 0.10% per side | Realistic taker + partial slippage |
| Stress | 0.20% per side | Taker + meaningful slippage on 4h crypto |

A claim of edge must hold at the **stress** level to be considered robust, but
it must at minimum survive the **mid** level to avoid immediate rejection.

## Position sizing and risk

| Item | Value |
|------|-------|
| Starting wallet | 10,000 USDT |
| Max open trades | 5 |
| Stake model | risk-based: `equity * risk_per_trade / stop_distance * price` |
| Risk per trade | 1% of equity at the ATR stop |
| Stop model | fixed 2 × ATR(20) from entry, plus a −30% hard backstop |
| Position adjustment | disabled (no pyramiding, no averaging) |
| Leverage | 1.0 (spot, long-only in the baseline) |
| `tradable_balance_ratio` | 0.99 |

Wallet sizing compounds: stake size grows with equity. This is intentional as
the base case, but it makes headline percentages large and hard to compare
across strategies. Every result therefore also reports the non-compounded
per-trade statistics (expectancy, profit factor, win rate).

## Metrics reported per experiment

Net return, CAGR, profit factor, max drawdown (trade-based and wallet-based),
trade count, win rate, expectancy, average and median trade, exposure, turnover,
total fees paid, Sharpe/Sortino (closed trades and daily wallet), SQN, per-trade
mean-profit p-value, yearly returns, per-pair returns, and the fee sensitivity
sweep.

## Reproducing a run

```powershell
# 1. make freqtrade importable (or skip if freqtrade is installed)
$env:PYTHONPATH = "C:\path\to\freqtrade-develop"

# 2. fetch the pre-registered data
./user_data/scripts/download_data.ps1

# 3. run the freeze-checked baseline
./user_data/scripts/run_experiment.ps1 -Experiment EXP-001
```

Freqtrade framework revision used for all 2026-09-16 baseline runs:
`freqtrade 2026.9-dev`, CCXT `4.5.71`, Python `3.12.10`, pandas `3.0.5`,
numpy `2.4.6`.

## Interpretation rules

1. A positive headline return is never sufficient on its own.
2. A result is compared against the pre-registered acceptance thresholds in the
   charter, criterion by criterion, and every criterion is reported.
3. Per-pair and per-year dispersion is reported even when the aggregate looks
   good, because a single pair or year can carry an entire result.
4. No result is described as "successful". Statuses are factual.
