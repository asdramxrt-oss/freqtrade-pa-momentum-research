# MECE Completion Wave — Research Audit & Phase-2 Integrity

**Branch:** `research/diagnostic-generalization`
**Wave start HEAD:** `5c3d4fbf90c3ec9aaf82129803647052fa62da88`
**Scope:** audit the repository and P3/Phase-2 research record, repair every
actionable integrity defect, and decide the smallest justified next step. No
production/live trading code. No new strategy. No Phase-3 execution.

## Cells

| Cell | Task | Status | Report |
|------|------|--------|--------|
| CELL-001 | Repository and research-state audit | COMPLETED | `.mece/cells/CELL-001/REPORT.md` |
| CELL-002 | P3 experiment audit | COMPLETED | `.mece/cells/CELL-002/REPORT.md` |
| CELL-003 | Architecture / next-step audit | COMPLETED | `.mece/cells/CELL-003/REPORT.md` |
| CELL-004 | DEC-007 diagnostic-only walk-forward | COMPLETED | `.mece/cells/CELL-004/REPORT.md` |
| CELL-005 | Final evidence synthesis and safety closure | COMPLETED | `.mece/cells/CELL-005/REPORT.md` |

Dependency order: CELL-001 → CELL-002 → CELL-003 (each consumes the previous
cell's fact/interpretation separation).

## Repairs applied in this wave

The **eight research files** below are the substantive repair targets (listed as
seven numbered items; item 2 covers the two `conftest.py` files). None is
production strategy logic; all are research infrastructure, tests, diagnostics or
research documentation. `WAVE.md`, `SYNTHESIS.md` and the `cells/*/REPORT.md`
files are **wave artifacts** produced by this wave (and are not counted among the
eight); they are kept uncommitted until the final commit.

1. `research_lib/strategies/FundingCarryResearch.py` — `ruff format` failure fixed
   (was the only unformatted file; blocked the research-branch CI check).
2. `conftest.py`, `tests/conftest.py` — freqtrade sibling-checkout discovery fixed
   so the full suite runs without an environment override (133 tests, previously
   90 + 2 skipped).
3. `user_data/scripts/diagnostics/diagnose_data_quality.py` — summary print no
   longer double-counts the overlapping pooled period.
4. `research/experiment_results/P3-EXP-002.md` — status header/verdict reconciled
   with the documented SI-4 correction and `P3-EXP-002.json` (FAIL, not PASS).
5. `research/experiment_results/P3-EXP-001.md` — stale "funding not applied"
   limitation reconciled with the corrected funding run.
6. `docs/EXPERIMENT_REGISTRY.md` — stale execution status/table/multiple-testing
   ledger updated to match the three executed P3 experiments (registry rule #4).
7. `docs/PHASE_D_CRITICAL_EVALUATION.md` — dated addendum recording which
   questions P3 execution has now answered (original text preserved).

## Verification performed

- Full Phase-2 diagnostic suite re-generated and compared to the committed JSONs:
  `data_quality`, `market_regimes`, `turtle_followthrough`, `pullback_geometry`,
  `trade_diagnostics`, `statistics` — **all EQUAL** (timestamps aside).
- `python -m pytest tests -q` → **133 passed**.
- `python -m ruff check .` → clean; `python -m ruff format --check .` → clean
  (**86 files already formatted**).
- Production strategies (`user_data/strategies/turtle`, `.../pullback`,
  `.../shared`) diff: **zero lines**.

## Scope confirmation

- **No additional Phase-3 experiment was executed during this MECE wave.** The
  only runs were read-only reproductions of the already-committed Phase-2
  diagnostics (`diagnose_*.py`) for comparison against the committed JSONs.
  `P3-EXP-004A/004B/005/006/007/008` were not started; N1/N2/N3 are proposals
  only (see CELL-003 and SYNTHESIS §7).
- **"No production/live code" means no production strategy logic changed.** The
  frozen production strategies (`user_data/strategies/turtle`,
  `.../pullback`, `.../shared`) diff to **zero lines**. The eight repaired files
  are research infrastructure, tests, diagnostics and research documentation —
  never production strategy logic.
- **Repository state.** At wave end the working tree is intentionally **not**
  clean: the eight repaired files plus `WAVE.md` and `SYNTHESIS.md` are modified
  (10 tracked files), and `.mece/PHASE_GATE.json`, the three `cells/*/TASK.md`
  inputs and the three `cells/*/REPORT.md` outputs are untracked. These MECE
  artifacts are kept present and uncommitted until the final commit.

See `.mece/SYNTHESIS.md` for conclusions and the recommended next step.

## Final-synthesis scope

CELL-005 consolidates the completed DEC-007 diagnostic-only walk-forward with
the already-recorded P3 and Phase-2 evidence.  It may update only MECE/research
governance artifacts and derived reports.  It must not start an experiment,
modify production strategy code or the frozen implementation specification,
change the phase gate, tune parameters, run hyperopt or retrain ML.  The wave
ends at the human decision gate.
