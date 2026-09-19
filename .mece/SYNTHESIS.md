# SYNTHESIS — MECE Completion Wave

| Field | Value |
|-------|-------|
| **Branch** | `research/diagnostic-generalization` |
| **Wave start HEAD** | `5c3d4fbf90c3ec9aaf82129803647052fa62da88` |
| **Cells completed** | CELL-001, CELL-002, CELL-003 (all have real `REPORT.md`) |
| **Production/live code changed** | **None** (verified: zero-line diff on frozen strategy subtrees) |
| **New strategy started** | None |
| **Phase-3 experiments executed** | None |

---

## 1. Completed work

### 1.1 Research-state audit (CELL-001) — pre-existing, verified
Repository structure, governance and **audit-time** state are documented in
`.mece/cells/CELL-001/REPORT.md` (the tracked working tree was clean *at that
moment, before the wave's repairs*; production baseline frozen at `12acbf7`; the
only untracked content then was the MECE task inputs). That "clean" observation
is a **pre-repair / historical** fact and does **not** describe the final
post-wave tree — see §3.1.

### 1.2 P3 experiment audit (CELL-002)
Audited P3-EXP-001/002/003 against their `.md`, `.json` and `.raw.json`
artifacts. Findings:
- All three are **FAIL** on the preregistered criteria.
- Measured numbers in every `.md` match the machine-readable JSON.
- Causality, cost handling, funding application and reproducibility checks pass;
  sample size, single-universe/single-window robustness and lack of a pristine
  holdout are the real limitations.
- Defects found (stale P3-EXP-002 PASS header, stale P3-EXP-001 funding
  limitation, stale registry) were repaired.

### 1.3 Architecture / next-step audit (CELL-003)
Determined, from verified evidence, that **no architecture is selected and no
component is justified**. Proposed the smallest evidence-driven next set (N1
walk-forward harness; N2 P3-EXP-006 estimator; N3 P3-EXP-007 regime) and
explicitly deferred cross-sectional momentum (documented near-identical prior
failure), combination (no validated component) and ML (must be last on a
validated baseline).

### 1.4 Repairs applied
See `.mece/WAVE.md` §"Repairs applied". **Eight research files** were the
substantive repair targets (research infrastructure, tests, diagnostics and
research documentation); none is production strategy logic and no measured
result was altered. `WAVE.md`, `SYNTHESIS.md` and the three `cells/*/REPORT.md`
files are **wave artifacts**, not repair targets.

## 2. Evidence

- **P3 results:** `research/experiment_results/P3-EXP-001..003.{md,json,raw.json}`;
  P3-EXP-002 stress PF 1.037 (`long_vol`) vs 1.259 (`long_raw`); P3-EXP-003
  `funding_fees_applied_usdt = −11305.87`.
- **Phase 2 diagnostic:** `research/experiment_results/PHASE2_DIAGNOSTIC.md` +
  seven `PHASE2_*.json`; `docs/EXPERIMENT_REGISTRY.md`;
  `docs/FROZEN_IMPLEMENTATION_SPEC.md`; `docs/PHASE_D_CRITICAL_EVALUATION.md`;
  `docs/EXTERNAL_EVIDENCE.md`; `research/decisions/DECISION_LOG.md`.
- **Data:** `user_data/data_p3/futures/` — 60 feathers, 10 perps × (4h OHLCV,
  4h/1h mark, index, premiumIndex, 1h funding).

## 3. Verification

Full Phase-2 diagnostic suite was **re-executed** and compared field-by-field to
the committed machine-readable outputs (timestamps excluded):

| Diagnostic | Result |
|------------|--------|
| `diagnose_data_quality.py` | EQUAL |
| `diagnose_market_regimes.py` | EQUAL |
| `diagnose_turtle_followthrough.py` | EQUAL |
| `diagnose_pullback_geometry.py` | EQUAL |
| `diagnose_trades.py` (8 backtests) | EQUAL |
| `diagnose_statistics.py` | EQUAL |

Recorded experiment numbers were reproduced exactly, including Turtle pooled
1,347 trades / PF 1.228 and Pullback pooled 607 / 1.567.

Other verification:

```powershell
python -m pytest tests -q          # 133 passed
python -m ruff check .             # All checks passed
python -m ruff format --check .    # 86 files already formatted
git diff HEAD -- user_data/strategies/turtle user_data/strategies/pullback user_data/strategies/shared
                                   # 0 lines (production untouched)
python -c "... compare committed P3 .md tables vs .raw.json ..."   # all match
```

(The formatter count includes Markdown: this repo's `ruff format` also formats
Python code blocks inside `.md` files, so the count tracks the MECE Markdown
artifacts as well as `.py`. The cell-time count was **84**; the wave recorded
**87** at its own close, while the final integrity pass observes **86** in the
frozen post-wave tree. The count is sensitive to exactly which artifacts are
present at the moment of the check and to the ruff version. "Clean" means zero
files would be reformatted.)

### 3.1 Pre-DEC-007 working-tree snapshot (intentionally not clean)

The final tree is **not** clean, and this synthesis does not claim otherwise.
`git status --short` at wave end:

- **Modified (tracked, 10):** the eight repaired research files —
  `conftest.py`, `tests/conftest.py`,
  `research_lib/strategies/FundingCarryResearch.py`,
  `user_data/scripts/diagnostics/diagnose_data_quality.py`,
  `research/experiment_results/P3-EXP-001.md`,
  `research/experiment_results/P3-EXP-002.md`,
  `docs/EXPERIMENT_REGISTRY.md`, `docs/PHASE_D_CRITICAL_EVALUATION.md` — plus
  the two wave artifacts `.mece/WAVE.md` and `.mece/SYNTHESIS.md`.
- **Untracked:** `.mece/PHASE_GATE.json` and the six
  `.mece/cells/CELL-00{1,2,3}/{TASK,REPORT}.md` files.

These MECE artifacts are **intentionally present and uncommitted until the final
commit**. This is the original pre-DEC-007 snapshot; the final closure artifacts
are recorded in §11 and CELL-005. The final integrity pass made documentation-only edits; it changed no
source code and no measured result. No new Phase-3 experiment was executed
during this wave (only read-only reproductions of the Phase-2 diagnostics).

### 3.2 Final integrity gate — result

- **Phase 2 is complete.** The Phase-2 diagnostic is reproducible end-to-end
  (§3) and its specification-consistent, deliberately non-strategy verdict is
  recorded in §4.
- **Required verification passed** on the frozen post-wave tree:
  `python -m pytest tests -q` → **133 passed**; `python -m ruff check .` →
  **All checks passed**; `python -m ruff format --check .` → **86 files already
  formatted (clean)**.
- **Production strategy logic has zero diff.**
  `git diff -- user_data/strategies/turtle user_data/strategies/pullback user_data/strategies/shared`
  returns **no lines** (confirmed by `--stat`/`--numstat`: empty).
- **The wave stops here — no automatic transition.** `.mece/PHASE_GATE.json`
  sets `allow_new_experiments = false` and `stop_after_phase_completion = true`.
  Nothing is started automatically. N1/N2/N3 and P3-EXP-004A/004B/005/006/007/008
  remain proposals only (§7) and require an explicit future decision.

## 4. Is Phase 2 complete? (honest assessment)

**The research Phase-2 diagnostic is complete and its outputs are reproducible.**
Every `PHASE2_*.json` regenerates identically from the committed scripts, and the
diagnostic reaches a deliberately non-strategy verdict ("multiple plausible
explanations") consistent with its own specification. This is supported by
evidence, not by assertion.

**Caveats that prevent a stronger claim:**
- The diagnostic re-runs are deterministic reproductions, **not new OOS
  evidence** (the specification says so explicitly).
- The 2025 and 2026 windows are consumed and non-pristine (SI-2 open); no pristine
  holdout exists.
- The two trade-level diagnostics require freqtrade + backtests; these were
  re-run and matched, but they reproduce historical windows only.
- No strategy is validated. Phase-2 completing does not mean any strategy works.

## 5. Unresolved blockers

1. **SI-2** — no pristine holdout; requires post-2026-09 data accrual.
2. **SI-3** — P3-EXP-004A/004B/005/006/007/008 remain unimplemented.
3. **Walk-forward harness** — mandated by frozen spec §9; only a README exists.
4. **Notion mirror** — the Git registry was corrected; the corresponding Notion
   DB was not edited in this session.
5. **GitHub remote 404** — local-only history; no off-machine backup.

## 6. Residual risks

- Regime/volatility work has high overfitting potential (many degrees of freedom);
  it must be pre-declared and boundary-fixed on train/validation only.
- Momentum/residual work carries factor-β look-ahead risk.
- `long_raw` full-sample significance (p=0.0020) is not an OOS pass.
- Carry is refuted only for the naive single-leg proxy implemented here.
- Any result fitted to 2025/2026 is void; only new data can confirm.
- Changing `conftest.py` bootstrap alters how tests discover freqtrade; it was
  made additive (new candidate paths appended) and verified by 133 passing tests.

## 7. Single next human decision (exact)

1. **Record that the programme remains paused with the Phase-2 gate closed until
   a pristine post-2026-09 holdout is available.**  Do not authorise
   P3-EXP-006/007/008, tuning, hyperopt, parameter/threshold search, or ML
   retraining from the current evidence.  Any later departure must be an
   explicit human decision recorded in `research/decisions/DECISION_LOG.md`.

## 8. Cell reports

- `.mece/cells/CELL-001/REPORT.md`
- `.mece/cells/CELL-002/REPORT.md`
- `.mece/cells/CELL-003/REPORT.md`

## 9. Session

OpenCode session ID: not exposed by this execution environment.

---

## 10. DEC-007 — diagnostic-only walk-forward (completed)

Governed by DEC-007. Implemented the frozen §9 harness and ran it on the
already-failed engines, unchanged: P3-EXP-001 long arms (`TurtleFuturesLong`,
`TurtleFuturesLongRaw`) and P3-EXP-003 (`FundingCarry`).

- Windows frozen before execution in
  `research/walk_forward/walk_forward_config.json` (anchored expanding IS,
  1-year OOS, 1-year step: W1 2023, W2 2024, W3 2025, W4 2026 partial);
  **W3/W4 NON-PRISTINE**.
- OOS positive-window counts: `long_vol` 2/4, `long_raw` 2/4, `carry` 3/4; none
  sign-consistent. Mean OOS/IS expectancy decay 0.044 / 0.113 / 0.463.
- Reproducibility: pass 2 identical to pass 1 (12 OOS runs).
- Parameter drift: NOT APPLICABLE (no parameter selected).
- **Diagnostic only.** No verdict changes; no engine is validated. Production
  subtrees zero-diff; `.mece/PHASE_GATE.json` unchanged; no commit/push.
- See `.mece/cells/CELL-004/REPORT.md` and
  `research/experiment_results/DEC-007_WALK_FORWARD.md`.

## 11. Final evidence synthesis — stop at the human gate

DEC-007 completes the only authorised follow-up to the prior MECE wave.  It
does not rescue or promote an engine: `long_vol` and `long_raw` have positive
OOS expectancy in only 2/4 windows, and `carry` in 3/4; each arm is
sign-inconsistent and its 2025–2026 windows are explicitly non-pristine.
Reproducing pass 1 in pass 2 establishes implementation reproducibility, not
an edge.  Parameter drift is not applicable because no parameter was selected
or tuned.

Taken with P3-EXP-001, P3-EXP-002 and P3-EXP-003 (all recorded FAIL), and the
Phase-2 diagnostic, the evidence supports no validated strategy, no promotion,
and no new experiment.  The only unconsumed confirmatory evidence would be a
fresh post-2026-09 holdout; the current record cannot create one.

The final evidence-synthesis stage is therefore a closure, not a transition:
the gate stays closed and the programme stops for the human decision in §7.
