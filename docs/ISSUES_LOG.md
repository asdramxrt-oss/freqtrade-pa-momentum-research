# Specification / data issue log

Issues that surfaced during research implementation. Recorded, not hidden. Per the
frozen-specification rule, the specification is **not** silently changed.

---

## SI-4 — Funding fees were silently not applied (RESOLVED 2026-09-16)

**Status:** resolved (data fixed); affected results re-run and superseded.

**What happened.** freqtrade backtesting applies funding PnL to held futures
positions via `_run_funding_fees` → `exchange.calculate_funding_fees`, using a
combined funding+**mark** frame. The exchange option
`mark_ohlcv_timeframe = "1h"` for Binance, so the engine **requires 1h mark
candles**. The Phase-3 download requested `-t 4h`, which stored mark at **4h
only**.

**Symptom.** No error was raised. Instead the engine logged, for every pair:

```
WARNING - No history for BTC/USDT:USDT, mark, 1h found. Use `freqtrade download-data` to download the data
```

`futures_data[pair]` was therefore empty and `calculate_funding_fees` returned
`0` for every trade. The futures backtests ran to completion with
**`funding_fees = 0` on every trade** — i.e. funding was silently excluded.

**Impact.**
- **P3-EXP-001** and **P3-EXP-002** were first recorded **without funding** applied.
- The first **P3-EXP-003** (carry) attempt was invalid: for carry, funding *is*
  the return, so a zero-funding run measures only directional PnL.
- The frozen specification §7 requires funding to be applied from real data to
  held positions, so those first results did not meet the specification.

**Detection.** The P3-EXP-003 runner deliberately reported total funding PnL;
it printed `funding_applied = 0 USDT`, which triggered investigation.

**Resolution.**
1. Downloaded 1h **mark** candles into `user_data/data_p3` (10 files, ~59k rows each).
2. Verified correctness: a manual funding computation for a real LINK short
   (2025-02-10 → 2025-02-24, 53.19 units) gives **0.4259 USDT**, and the engine now
   reports exactly **0.4259** for that trade.
3. Re-ran **P3-EXP-001** (16 runs), **P3-EXP-002** (14 runs) and **P3-EXP-003**
   (4 runs) with funding applied. Prior numbers are **superseded**, not deleted.

**Lesson / guard.** Any futures backtest must confirm `funding_fees != 0` when
funding data is expected; absence of an error is **not** evidence that funding was
modeled. The P3 runners now report total applied funding.

**No specification text was changed** — the specification already required
funding; the data/engine setup was corrected to match it.
