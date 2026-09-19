# CELL-004 — DEC-007 diagnostic-only walk-forward

| Field | Value |
|-------|-------|
| **Cell** | CELL-004 |
| **Status** | COMPLETED |
| **Branch** | `research/diagnostic-generalization` |
| **Governance** | DEC-007 (diagnostic-only; not validation/promotion/verdict) |
| **Frozen methodology** | `docs/FROZEN_IMPLEMENTATION_SPEC.md` §9 |
| **Production code touched** | No |
| **Gate changed** | No |

## What was done

Implemented and ran the frozen §9 walk-forward harness on the two
already-implemented, already-failed engines, implementations unchanged:

- `TurtleFuturesLong` (`long_vol`), `TurtleFuturesLongRaw` (`long_raw`) — P3-EXP-001
- `FundingCarry` (`carry`) — P3-EXP-003

Windows were frozen before execution in
`research/walk_forward/walk_forward_config.json` (anchored expanding in-sample,
1-year OOS, 1-year step; W1 2023, W2 2024, W3 2025, W4 2026 partial). W3/W4 are
NON-PRISTINE.

## Results (OOS; observed facts)

| Arm | W1 2023 | W2 2024 | W3 2025 (NP) | W4 2026 (NP) | Positive OOS |
|-----|---------|---------|--------------|--------------|--------------|
| `long_vol` | PF 1.1505, +16.84% | PF 1.5956, +66.97% | PF 0.8327, −16.18% | PF 0.7560, −14.76% | 2/4 |
| `long_raw` | PF 1.1655, +9.53% | PF 1.6104, +33.68% | PF 0.8842, −6.47% | PF 0.8208, −6.52% | 2/4 |
| `carry` | PF 2.5029, +80.33% | PF 2.8116, +57.90% | PF 0.6725, −24.84% | PF 1.0014, +0.06% | 3/4 |

- Mean OOS/IS expectancy decay: `long_vol` 0.0444, `long_raw` 0.1129, `carry` 0.4628.
- Parameter drift: **NOT APPLICABLE** — no parameter was selected or tuned.
- Reproducibility: pass 2 reproduced pass 1 **identically** (12 OOS runs compared).
- Funding applied (SI-4 guard): all runs report non-zero applied funding; carry
  funding PnL is negative in 2023/2024 (paid funding) and positive in 2025/2026.

## Interpretation (diagnostic only)

The walk-forward shows the same shape as the recorded failures: early OOS
windows (2023, 2024) are positive, while the recent consumed windows (2025,
2026) are weak or negative; no engine is sign-consistent across windows. This is
**not** validation and does **not** change any verdict — all engines remain FAIL.
A pristine conclusion still requires post-2026-09 data (SI-2).

## Artifacts

- `research/walk_forward/walk_forward_config.json`
- `research/walk_forward/run_walk_forward.py`
- `tests/research/test_walk_forward.py` (14 tests)
- `research/experiment_results/DEC-007_walk_forward.raw.json`
- `research/experiment_results/DEC-007_walk_forward.json`
- `research/experiment_results/DEC-007_WALK_FORWARD.md`

## Stop

The programme stops at the next human decision gate. No promotion, no commit/push.
