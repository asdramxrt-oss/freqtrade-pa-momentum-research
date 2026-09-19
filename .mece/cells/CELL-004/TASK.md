# CELL-004 — DEC-007 diagnostic-only walk-forward

| Field | Value |
|-------|-------|
| **Cell** | CELL-004 |
| **Status** | IN PROGRESS |
| **Branch** | `research/diagnostic-generalization` |
| **Governance** | DEC-007 (diagnostic-only; not validation/promotion/verdict) |
| **Frozen methodology** | `docs/FROZEN_IMPLEMENTATION_SPEC.md` §9 |
| **Production code touched** | No |

## Task

Implement and run the frozen §9 walk-forward harness for the two
already-implemented, already-failed engines, with parameters unchanged:

- `TurtleFuturesLong` (`long_vol`) and `TurtleFuturesLongRaw` (`long_raw`) — P3-EXP-001
- `FundingCarry` (`carry`) — P3-EXP-003

Report per-window return, profit factor, trade count, maximum drawdown and
expectancy, plus stability, decay and reproducibility. Windows are frozen in
`research/walk_forward/walk_forward_config.json` before execution; 2025–2026
windows are NON-PRISTINE. No gate change, no promotion, no parameter search.

## Guardrails

- Production strategy subtrees must remain zero-diff.
- `.mece/PHASE_GATE.json` unchanged.
- P3 engine implementations/configs used unchanged.
- P3-EXP-006/007/008 not executed.
- No commit/push; stop at the next human gate.

## Deliverables

- `research/walk_forward/walk_forward_config.json`
- `research/walk_forward/run_walk_forward.py`
- `tests/research/test_walk_forward.py`
- `research/experiment_results/DEC-007_walk_forward.raw.json`
- `research/experiment_results/DEC-007_walk_forward.json`
- `research/experiment_results/DEC-007_WALK_FORWARD.md`
