# Futures data availability — audit (Phase 3, evidence)

Measured on 2026-09-16 by attempting real downloads and inspecting the stored
files. This is an evidence record, not a plan.

## What was downloaded

Command (same pair universe and timeframe as the programme):

```powershell
python -m freqtrade download-data --userdir user_data -c user_data/configs/EXP-003.json `
    -t 4h --trading-mode futures `
    --candle-types funding_rate mark premiumIndex index `
    --timerange 20190101-20260916
```

## Measured coverage (per pair, 10 USDT perpetuals)

| Candle type | Timeframe | Rows/pair | Coverage | Usable? |
|-------------|-----------|-----------|----------|---------|
| `funding_rate` | `1h` (one row per funding event) | 6,555–7,690 | BTC 2019-09-10; ETH 2019-11-27; XRP/ADA/LINK 2020-01; BNB 2020-02; DOGE 2020-07; DOT/SOL 2020-08/09 → 2026-09-16 | **Yes** |
| `mark` | `4h` | 13,110–14,754 | BTC/BNB/ETH/XRP 2019-12-23; others perp listing → 2026-09-16 | **Yes** |
| `index` | `4h` | 13,110–14,754 | as mark | **Yes** |
| `premiumIndex` | `4h` | ~13,100–14,700 | as mark | **Yes** |
| `open_interest` | `4h` | **none** | — | **No** |

`funding_rate` history begins at each perpetual's Binance listing, not 2019-01-01
for all pairs; this is a real constraint on any carry study (the early
cross-section is only BTC/ETH/XRP/ADA/LINK/BNB).

## Open interest is NOT retrievable

freqtrade/ccxt attempt to page Binance `openInterestHist` from 2019 returns:

```
BadRequest: binance {"msg":"parameter 'startTime' is invalid.","code":-1130}
```

Binance only retains a short open-interest window via the public endpoint, so
**long-history OI is unavailable**. Consequence: any open-interest-based
candidate is **INSUFFICIENT DATA** and cannot be tested on this universe/period.
No synthetic OI will be manufactured.

## Important caveat: the futures OHLCV on disk is a spot mirror

`user_data/data/binance/futures/*-4h-futures.feather` was produced by
`prepare_futures_data.py` as a **byte-identical copy of the spot candles**
(documentedly, EXP-003 spec §6). Real Binance futures OHLCV was **not**
downloaded, because downloading it would overwrite those filenames and break the
recorded reproduction of EXP-003/EXP-004.

**Implication:** carry/basis studies can use the **real** `funding_rate`, `mark`,
`premiumIndex` and `index` data now present. But any production-grade futures
work should eventually use **real futures OHLCV**, and that switch must be a
recorded decision because it changes the price series behind any result.

## What this changes

| Candidate | Before | After |
|-----------|--------|-------|
| Carry / perpetual funding | INSUFFICIENT DATA | **UNTESTED (data now available)** |
| Basis / term structure | INSUFFICIENT DATA | **UNTESTED (data now available)** |
| Open-interest + price momentum | INSUFFICIENT DATA | **INSUFFICIENT DATA (confirmed; API limit)** |

Funded carry/basis research is now feasible from perp listing; OI-based research
is not, on this exchange and period.
