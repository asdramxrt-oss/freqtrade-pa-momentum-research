# DEC-007 — diagnostic-only walk-forward

**Status:** DIAGNOSTIC ONLY. This is not validation, not a promotion and not a strategy verdict. All engines were already FAIL on their preregistered criteria (P3-EXP-001 long arms, P3-EXP-003 carry).

Frozen methodology: `docs/FROZEN_IMPLEMENTATION_SPEC.md` section 9 (anchored expanding in-sample, 1-year out-of-sample, 1-year step). Governance: DEC-007. Windows are frozen in `research/walk_forward/walk_forward_config.json` before execution.

**NON-PRISTINE:** windows W3, W4 overlap the 2025-2026 period already observed by EXP-001..004 and PHASE 2. They are reported as non-pristine diagnostics, never as clean out-of-sample evidence.

## long_vol — TurtleFuturesLong (P3-EXP-001)

| Window | Pristine? | IS trades | IS PF | IS ret % | OOS trades | OOS PF | OOS ret % | OOS DD % | OOS expectancy | OOS p | OOS funding USDT |
|--------|-----------|----------:|------:|---------:|-----------:|-------:|----------:|---------:|---------------:|------:|----------------:|
| W1 (2023) | yes | 611 | 1.2511 | 998.78 | 179 | 1.1505 | 16.84 | 32.01 | 9.4098 | 0.5681 | -340.63 |
| W2 (2024) | yes | 803 | 1.2195 | 1147.92 | 189 | 1.5956 | 66.97 | 13.73 | 35.4362 | 0.0729 | -831.28 |
| W3 (2025 (PHASE 2 'C', consumed)) | NO | 1001 | 1.3022 | 2008.34 | 185 | 0.8327 | -16.18 | 31.37 | -8.7435 | 0.4219 | -194.81 |
| W4 (2026 partial (PHASE 2 'F', consumed)) | NO | 1195 | 1.1959 | 1701.41 | 123 | 0.7560 | -14.76 | 30.01 | -12.0032 | 0.3963 | -104.97 |

**OBSERVED FACT (stability):** 2/4 OOS windows positive; sign-consistent = False; OOS PF range = 0.8396; OOS return range = [-16.18%, 66.97%].
**OBSERVED FACT (decay):** mean OOS/IS expectancy ratio = 0.0444.
**NOT APPLICABLE (parameter drift):** no parameter was selected or tuned on any window; the engines use frozen fixed parameters.

## long_raw — TurtleFuturesLongRaw (P3-EXP-001)

| Window | Pristine? | IS trades | IS PF | IS ret % | OOS trades | OOS PF | OOS ret % | OOS DD % | OOS expectancy | OOS p | OOS funding USDT |
|--------|-----------|----------:|------:|---------:|-----------:|-------:|----------:|---------:|---------------:|------:|----------------:|
| W1 (2023) | yes | 643 | 1.8306 | 186.84 | 230 | 1.1655 | 9.53 | 17.17 | 4.1448 | 0.4893 | -166.78 |
| W2 (2024) | yes | 873 | 1.6941 | 196.21 | 221 | 1.6104 | 33.68 | 6.71 | 15.2414 | 0.0650 | -381.04 |
| W3 (2025 (PHASE 2 'C', consumed)) | NO | 1094 | 1.6812 | 230.05 | 227 | 0.8842 | -6.47 | 17.55 | -2.8482 | 0.5342 | -119.35 |
| W4 (2026 partial (PHASE 2 'F', consumed)) | NO | 1320 | 1.5676 | 223.40 | 165 | 0.8208 | -6.52 | 17.99 | -3.9540 | 0.4165 | -62.73 |

**OBSERVED FACT (stability):** 2/4 OOS windows positive; sign-consistent = False; OOS PF range = 0.7896; OOS return range = [-6.52%, 33.68%].
**OBSERVED FACT (decay):** mean OOS/IS expectancy ratio = 0.1129.
**NOT APPLICABLE (parameter drift):** no parameter was selected or tuned on any window; the engines use frozen fixed parameters.

## carry — FundingCarry (P3-EXP-003)

| Window | Pristine? | IS trades | IS PF | IS ret % | OOS trades | OOS PF | OOS ret % | OOS DD % | OOS expectancy | OOS p | OOS funding USDT |
|--------|-----------|----------:|------:|---------:|-----------:|-------:|----------:|---------:|---------------:|------:|----------------:|
| W1 (2023) | yes | 165 | 1.5249 | 198.25 | 61 | 2.5029 | 80.33 | 20.52 | 131.6815 | 0.1539 | -129.37 |
| W2 (2024) | yes | 221 | 1.7154 | 381.52 | 38 | 2.8116 | 57.90 | 13.56 | 152.3574 | 0.1538 | -422.85 |
| W3 (2025 (PHASE 2 'C', consumed)) | NO | 262 | 1.8702 | 620.20 | 82 | 0.6725 | -24.84 | 31.76 | -30.2929 | 0.2640 | 142.60 |
| W4 (2026 partial (PHASE 2 'F', consumed)) | NO | 348 | 1.3735 | 448.77 | 84 | 1.0014 | 0.06 | 4.63 | 0.0671 | 0.9964 | 87.34 |

**OBSERVED FACT (stability):** 3/4 OOS windows positive; sign-consistent = False; OOS PF range = 2.1391; OOS return range = [-24.84%, 80.33%].
**OBSERVED FACT (decay):** mean OOS/IS expectancy ratio = 0.4628.
**NOT APPLICABLE (parameter drift):** no parameter was selected or tuned on any window; the engines use frozen fixed parameters.

## Reproducibility

```json
{
  "passes_present": [
    "pass1",
    "pass2"
  ],
  "result": "IDENTICAL",
  "compared_runs": 12
}
```

## LIMITATIONS

- Diagnostic only; no engine here passed its preregistered criteria.
- 2025-2026 windows are non-pristine (already consumed).
- No pristine post-2026-09 holdout exists (SI-2).
- Early windows are dominated by the first-listed pairs; later-listed pairs are absent before their listing date.
- No parameter search was performed, so this cannot select a configuration.
