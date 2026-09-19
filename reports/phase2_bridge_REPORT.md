# Phase-2 Automation Bridge — REPORT

**Run ID:** `phase2_bridge`  
**Generator:** `automation.report` (deterministic, derived view)  
**Source of truth:** `research/experiment_results/`  

> This report is a derived view. If it disagrees with a recorded result, the recorded result wins.

## Governance

| Field | Value |
|-------|-------|
| Phase | PHASE2 |
| Allow new experiments | False |
| Stop after phase completion | True |

## Artifacts

| Experiment | Status | Verdict | Production changed | Funding applied |
|------------|--------|---------|--------------------|-----------------|
| P3-EXP-001 | COMPLETED | FAIL | no | yes |
| P3-EXP-002 | COMPLETED | FAIL | no | yes |
| P3-EXP-003 | COMPLETED | FAIL | no | yes |

### Decisions

- **P3-EXP-001:** FAIL.
- **P3-EXP-002:** FAIL.
- **P3-EXP-003:** FAIL.

## Validation

| Check | Result | Detail |
|-------|--------|--------|
| gate_present | PASS | phase=PHASE2 |
| production_untouched | PASS | clean |
| required_artifacts | PASS | 13 present |
| json_artifacts | PASS | 3 artifacts consistent |
| bridge_safety | PASS | no dangerous execution patterns |

## Integrity

- Input digest (sha256): `ce8927171812834c6263730f4f9dfa77dedfe5a21646f8adbcc20a75aa691db7`
- Production strategy subtrees: asserted untouched by `automation.validation`.
- Research-only: no live-trading code path exists in this bridge.

## Next step

- Proposal written to: `C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research\.mece\NEXT_TASK.md` (PROPOSAL ONLY — not executed).

## Notices

- The bridge never executes the next task; a human decides.
- No experiment is started while the phase gate forbids it.
