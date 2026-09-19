# CELL-005 — Final evidence synthesis and safety closure

| Field | Value |
|---|---|
| **Cell** | CELL-005 |
| **Status** | COMPLETED |
| **Run ID** | `final_evidence_synthesis` |
| **Gate** | `PHASE2`; `allow_new_experiments=false`; `stop_after_phase_completion=true` |
| **Experiment execution** | None |

## Outcome

DEC-007 is consolidated into `.mece/SYNTHESIS.md`.  Its walk-forward result is
diagnostic only: none of the three already-failed engines is sign-consistent
across the four frozen windows, W3/W4 remain non-pristine, and the identical
second pass establishes reproducibility rather than validation.  No strategy is
promoted and no follow-on experiment is authorised.

The existing controller completed its safe path with run ID
`final_evidence_synthesis`: gate, production, required-artifact, recorded-JSON
and bridge-safety checks all passed.  It wrote the derived report and refreshed
the proposal; the proposal is marked `executed=false` and the closed gate blocks
execution.

## Verification

- `tests/research/test_walk_forward.py` plus bridge unit/integration tests:
  **86 passed**.
- Relevant bridge/walk-forward lint: **passed**.
- Relevant bridge/walk-forward format check: **23 files already formatted**.
- Frozen production strategy subtrees: controller validation **PASS**.
- `docs/FROZEN_IMPLEMENTATION_SPEC.md`: retained as zero-diff (verified after
  this cell).

## Scope and stop

No P3-EXP-006/007/008, tuning, hyperopt, parameter/threshold search or ML
retraining was run.  No commit, push, merge, deployment, gate transition,
production-strategy change or frozen-spec change occurred.

The full suite was attempted but is not a clean result in this local environment:
175 tests passed and 44 strategy tests errored while importing Freqtrade because
installed `pydantic` requires `pydantic-core 2.46.4` but `2.41.5` is present.
This environmental dependency defect was left untouched.

The programme stops at the single human decision recorded in SYNTHESIS §7:
retain the closed gate and pause for a pristine post-2026-09 holdout.
