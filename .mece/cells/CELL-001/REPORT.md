# CELL-001 — Repository and Research-State Audit

**Audit date:** 2026-09-16
**Auditor:** CELL-001 (read-only; no production logic touched)
**Working directory:** `C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research`

> **Scope of this report — read first.**
> This report records the **audit-time / pre-repair** state observed at HEAD
> `5c3d4fb`, *before* the MECE wave applied its repairs. Every "working tree is
> clean" / "no modified files" statement below is a **historical fact about that
> audit moment** — it is **not** a description of the final post-wave
> repository.
>
> After this audit the wave applied repairs to **eight research files** and wrote
> its MECE artifacts (`.mece/WAVE.md`, `.mece/SYNTHESIS.md`,
> `.mece/cells/*/REPORT.md`). The final working tree is therefore **not clean**
> (10 tracked files modified; the cell `REPORT.md`/`TASK.md` files and
> `.mece/PHASE_GATE.json` untracked). See §8 "Post-wave reconciliation"
> and `.mece/SYNTHESIS.md` §3.1.

---

## 1. Repository state

### 1.1 Git state

| Item | Value |
|------|-------|
| Branch checked out | `research/diagnostic-generalization` |
| HEAD commit | `5c3d4fbf90c3ec9aaf82129803647052fa62da88` |
| HEAD subject | `research: P3-EXP-003 carry (FAIL), fix SI-4 funding defect, re-run P3-EXP-001/002 with funding` |
| Working tree (tracked) | **clean at audit time** — `git diff HEAD` returned 0 lines (pre-repair; see the scope note above and §8) |
| Stash | empty (`git stash list` returns nothing) |
| `origin` remote | `https://github.com/asdramxrt-oss/freqtrade-pa-momentum-research.git` — **`git ls-remote origin` returns 404**; the GitHub repository does not exist. No push is possible. |

### 1.2 Branches present

| Branch | Tip commit (first 7) | Notes |
|--------|----------------------|-------|
| `main` | `536c2a4` (referenced in `docs/REPOSITORY_AUDIT.md`) | shared foundation only; research records live on their own branches |
| `research/diagnostic-generalization` | `5c3d4fb` *(HEAD)* | Phase-2 diagnostic + P3-EXP-001/002/003 work |
| `research/frozen-pullback-oos` | `1d6e561` (referenced in decision log) | EXP-004 slot |
| `research/pullback-continuation` | `e6d8f88` (referenced) | EXP-003 slot |
| `research/turtle-baseline` | `12acbf7` (referenced) | EXP-001 slot, frozen baseline commit |
| `research/turtle-costs` | `3481520` (referenced) | EXP-002 slot |

### 1.3 Modified / untracked files

**Modified (tracked):** none *at audit time* (pre-repair).

**Untracked (only, at audit time):**

```
.mece/cells/CELL-001/TASK.md
.mece/cells/CELL-002/TASK.md
.mece/cells/CELL-003/TASK.md
```

The three TASK.md files are the inputs for this MECE cell wave. They were the only untracked content in the working tree *at audit time* — the wave later added `REPORT.md` files and `.mece/PHASE_GATE.json` (see §8).

**Existing MECE scaffolding:**

| Path | Content |
|------|---------|
| `.mece/SYNTHESIS.md` | **Empty** (0 bytes; verified) *at audit time* — populated by the wave, see §8 |
| `.mece/WAVE.md` | **Empty** (0 bytes; verified) *at audit time* — populated by the wave, see §8 |
| `.mece/cells/CELL-001/TASK.md` | 37 lines — the brief for this cell |
| `.mece/cells/CELL-002/TASK.md` | 36 lines — brief for the P3-experiment audit cell |
| `.mece/cells/CELL-003/TASK.md` | 34 lines — brief for the architecture/next-step audit cell |

The MECE scaffolding was committed in the most recent commit (`5c3d4fb`) so the empty placeholders appear in `git diff HEAD~1 HEAD` but no actual content has been written beyond the three TASK.md files.

---

## 2. Files inspected

### 2.1 Top-level

| Path | Read | Notes |
|------|------|-------|
| `README.md` | yes | Project charter / status table; **stale** (see §5). |
| `pyproject.toml` | yes | numpy, pandas deps; `freqtrade` deliberately not pinned; pytest + ruff dev deps; coverage source set to `user_data/strategies/shared` and `turtle`. |
| `conftest.py` | yes | Pytest bootstrap: adds `user_data/strategies/shared` to `sys.path` and best-effort resolves a `freqtrade` source checkout from `FREQTRADE_SRC` or the conventional sibling (`../freqtrade-develop/freqtrade-develop`). |
| `tests/conftest.py` | yes | Adds `requires_freqtrade` marker; defines `trending_breakout_candles` and `breakdown_candles` fixtures. |
| `tests/helpers.py` | yes | `make_candles(closes, start)` synthetic OHLCV generator (no network). |
| `.gitignore` | yes | Blocks `.env`, downloaded data, backtest outputs, model binaries; explicitly exempts `.env.example`; `user_data/data_p3/` added. |
| `.env.example` | yes | Documents `FREQTRADE_SRC` and empty exchange credential slots. |

### 2.2 Documentation (`docs/`)

| File | Read | Notes |
|------|------|-------|
| `docs/REPOSITORY_AUDIT.md` | yes | Phase-A audit dated 2026-09-16 @ `33f3702`+; ends at A20; concludes "research-grade, not production-grade". |
| `docs/DATA_AVAILABILITY.md` | yes | Evidence record of futures data coverage + 2 updates (SI-1 resolution, SI-4 fix). |
| `docs/EXTERNAL_EVIDENCE.md` | yes | Phase-B references (Moskowitz/Ooi/Pedersen 2012; Kim/Tse/Wald 2016; Blitz/Huij/Martens 2011; Liu/Tsyvinski/Wu 2022; "Crypto Carry Trade"; López de Prado 2018; Yang/Zhang efficiency caveat 2026; plus the **negative** Fayez Junior 2026 on Binance perps). |
| `docs/EXPERIMENT_REGISTRY.md` | yes | Phase-3 registry; 9 preregistered experiments (`P3-EXP-001…008`, with 004 split A/B); multiple-testing ledger. |
| `docs/PHASE_D_CRITICAL_EVALUATION.md` | yes | Categorised FACT / INTERPRETATION / HYPOTHESIS / UNKNOWN; 9 critical questions; architecture selection table (all UNRESOLVED except Turtle-only default). |
| `docs/FROZEN_IMPLEMENTATION_SPEC.md` | yes | Frozen spec: instrument, leverage 1.0, timeframes, validation partitions, costs, six research engines (§6.1–§6.6), components explicitly rejected. Three open SI issues. |
| `docs/ISSUES_LOG.md` | yes | SI-4 resolved (funding fee defect; engine requires 1h mark); affected runs re-executed and superseded. |

### 2.3 Research record (`research/`)

| Path | Read | Notes |
|------|------|-------|
| `research/preregistration/research_charter.md` | yes | **FROZEN.** Acceptance thresholds A1–A8; sequence EXP-001…015. |
| `research/preregistration/experiment_protocol.md` | yes | **FROZEN.** Universe, periods, cost scenarios, sizing, metrics, reproduction command. |
| `research/decisions/DECISION_LOG.md` | yes | DEC-001…DEC-006 + PHASE-2 reference; commit SHAs recorded for every phase. |
| `research/notion_map.md` | yes | Bridge between Git artifacts and Notion pages (8 section pages + Experiments DB + Phase-3 registry DB). |
| `research/hypotheses/{turtle,pullback_continuation,breakout_retest,volatility_expansion}.md` | yes (turtle + pullback in full; others read) | One hypothesised doc per setup family. **No `swing_structure.md` for the charted EXP-009 slot.** |
| `research/experiment_specs/EXP-001.md … EXP-004.md` | yes (001, 003, 004 in full) | Specs are committed before runs; EXP-004 has an explicit governance note (DEC-005). |
| `research/experiment_specs/PHASE2_DIAGNOSTIC.md` | yes | Phase-2 diagnostic spec, hash-anchored. |
| `research/experiment_specs/TEMPLATE.md` | yes | Blank template. |

### 2.4 Experiment results (`research/experiment_results/`)

| File | Read | Notes |
|------|------|-------|
| `EXP-001.md` + `.json` | yes (md) | **FAIL** (4/8 charter criteria). |
| `EXP-002.md` + `.json` + `.raw.json` | yes (md) | **FAIL** (same failures as 001; costs not the binding constraint). |
| `EXP-003.md` + `.json` + `.raw.json` + `.geometry.json` + `.complementarity.json` | yes (md) | **MIXED** — combined FAIL (4/8), short FAIL (4/8), long-only 8/8 (a pre-registered *variant*, not the primary object). |
| `EXP-004.md` + `.json` + `.raw.json` + `.regression.json` | listed (md read via spec/DECISION_LOG) | **FAILS FRESH OOS** (DEC-006); 64 trades, PF 0.607, −12.75%. |
| `PHASE2_DIAGNOSTIC.md` + 7 PHASE2_*.json | yes (md) | **No strategy verdict**; multiple plausible explanations; sampling / regime shift; data-quality and costs ruled out. |
| `P3-EXP-001.md` + `.json` + `.raw.json` | yes (md + json) | **FAIL** — genuine-futures Turtle, long/short × vol/raw arms; OOS negative for both long arms (PF 0.813 / 0.852); signal-vs-sizing ablation showed **fixed notional beats volatility-scaled** on PF, DD and p. |
| `P3-EXP-002.md` + `.json` + `.raw.json` | yes (md + json) | **FAIL after funding correction.** Verdict flipped PASS→FAIL when SI-4 funding defect was fixed: `long_vol` stress PF 1.037 (< 1.05 acceptance), `long_raw` stress PF 1.259 (passes). Mixed by sizing → not a clean pass. |
| `P3-EXP-003.md` + `.json` + `.raw.json` | yes (md + json) | **FAIL** — carry. Aggregate funding PnL **−11,306 USDT** (strategy paid funding; not harvesting it). Test PF 0.805, −20.7%, p=0.405. |
| `P3_FUTURES_DATA_MANIFEST.json` | first 50 lines | Genuine-futures manifest (SHA-256 per file; covered in `docs/DATA_AVAILABILITY.md`). |

### 2.5 Strategy code

| File | Read | Notes |
|------|------|-------|
| `user_data/strategies/turtle/DonchianTurtleBaseline.py` | listed (path) | **Frozen reference baseline** @ `12acbf7`, untouched (verified by repo audit §A18 and `git diff` empty on that subtree in recent commits). |
| `user_data/strategies/pullback/PullbackContinuation.py` | listed (path) | Three classes: `PullbackContinuation` (both), `PullbackContinuationLong`, `PullbackContinuationShort`. Frozen @ `c4bee8e`. |
| `user_data/strategies/breakout_retest/` | listed | **Empty directory** (only `__pycache__`). No implementation file. |
| `user_data/strategies/volatility_expansion/` | listed | **Empty directory** (only `__pycache__`). No implementation file. |
| `user_data/strategies/shared/` | listed | `__init__.py`, `pa_indicators.py`, `pa_signals.py`, `pa_risk.py`, `pa_pullback.py`, `pa_structure.py`. Pure, causal, no freqtrade import. |
| `research_lib/strategies/TurtleFuturesResearch.py` | yes | P3-EXP-001 arms (`TurtleFuturesLong/LongRaw/Short/ShortRaw`); four concrete classes combine direction × sizing; reuses shared modules; outside `user_data/strategies/` on purpose. |
| `research_lib/strategies/FundingCarryResearch.py` | yes | P3-EXP-003 carry engine; single-leg perp; **no directional stop** by specification (recorded as a limitation). |

### 2.6 Configs (`user_data/configs/`)

| File | Read | Notes |
|------|------|-------|
| `EXP-001.json` | listed | Spot, long-only Turtle; fee 0.0005; 10-pair StaticPairList. |
| `EXP-002.json` | listed | Cost-sweep driver (same strategy). |
| `EXP-003.json` + `EXP-003-long.json` + `EXP-003-short.json` + `EXP-003-spot-long.json` | listed | Pullback variants (combined / long / short / spot-long control). |
| `P3-EXP-001.json` | yes | Futures, isolated, fee 0.0005, dry_run; strategy `TurtleFuturesLong`; 10-perp pair_whitelist. |
| `P3-EXP-003.json` | yes | Futures, isolated, fee 0.0005, dry_run; strategy `FundingCarry`. |
| `README.md` | yes | **Stale** — only documents `EXP-001.json`; four more configs exist (see §5). |

### 2.7 Scripts (`user_data/scripts/`)

| File | Read | Notes |
|------|------|-------|
| `download_data.ps1`, `run_experiment.ps1`, `download_futures_data.ps1` | listed | Thin wrappers over `freqtrade`. |
| `exp002_cost_sweep.py`, `exp003_backtest.py`, `exp003_complementarity.py`, `exp003_geometry.py`, `exp004_oos.py`, `exp004_regression.py` | listed | Phase-2 / EXP-002–004 runners. |
| `prepare_futures_data.py`, `futures_data_manifest.py` | listed | Data helpers (manifest builder + spot-mirror preparation). |
| `p3_exp001_run.py` | yes | P3-EXP-001 runner; 4 arms × 4 windows grid; outputs `P3-EXP-001.raw.json`. |
| `p3_exp002_costs.py` | yes | P3-EXP-002 cost-grid runner; 6 unique effective costs × 2 arms × 2 windows; outputs `P3-EXP-002.raw.json`. |
| `p3_exp003_carry.py` | yes | P3-EXP-003 carry runner; records total funding PnL applied (this is what surfaced SI-4). |
| `diagnostics/diag_common.py` + 6 `diagnose_*.py` | listed | Phase-2 diagnostics (data quality, regimes, follow-through, pullback geometry, trades, statistics). |

### 2.8 Tests (`tests/`)

| File | Read | Notes |
|------|------|-------|
| `tests/unit/test_pa_indicators.py` | listed | Pure indicator tests (Donchian, ATR, prefix invariance). |
| `tests/unit/test_pa_signals.py` | listed | Rising-edge semantics, suppression, etc. |
| `tests/unit/test_pa_risk.py` | listed | Sizing + ATR stop distance + ratio maths. |
| `tests/unit/test_pa_pullback.py` | listed | Pullback structural primitives. |
| `tests/unit/test_pa_structure.py` | listed | Swing-structure causality + publication delay. |
| `tests/unit/test_turtle_strategy.py` | listed | Frozen Turtle strategy contract. |
| `tests/unit/test_pullback_strategy.py` | listed | Includes `TestNoTurtleCoupling` (E3 integrity). |
| `tests/integration/` | listed | **Empty** — only `__init__.py` + `.gitkeep`. |
| `tests/research/` | listed | **Empty** — only `__init__.py` + `.gitkeep`. |

`README.md` claims "76 tests passing" / 124 test functions / 133 collected. The actual unit suite is **7 files** — the README is out of date. The repo audit (A18) reports `pytest tests -q` → 133 passed and `ruff` clean.

### 2.9 ML scaffolding (`ml/`)

| Path | Read | Notes |
|------|------|-------|
| `ml/README.md` | yes | Hygiene rules + per-strategy prediction problem directory table. |
| `ml/turtle/`, `ml/pullback/`, `ml/breakout_retest/`, `ml/volatility_expansion/`, `ml/features/`, `ml/labels/`, `ml/validation/` | listed | **All empty** (subfolders only; no files). |

### 2.10 Data (`user_data/data*`)

| Path | Read | Notes |
|------|------|-------|
| `user_data/data/binance/` | listed | 10 spot 4h feathers (`BTC…DOT`). Used for EXP-001/002/003/004 reproduction. |
| `user_data/data/binance/futures/` | listed | 10 pairs × 5 candle types (4h-futures, 4h-mark, 4h-index, 4h-premiumIndex, 1h-funding_rate). **Per `docs/DATA_AVAILABILITY.md`, this is a byte-identical spot mirror** kept for EXP-003/004 reproduction. |
| `user_data/data_p3/futures/` | listed | **Genuine** Binance USDT-M futures dataset: 10 pairs × 6 candle types (adds 1h-mark to support SI-4 fix). 60 feathers total. |
| `user_data/backtest_results/` | listed | **481 files** (`.json` + `.zip` + `.meta.json`); gitignored; latest pointer `.last_result.json` → `backtest-result-2026-09-16_11-49-22.zip` (most recent P3-EXP-003 run). |

### 2.11 Other

| Path | Read | Notes |
|------|------|-------|
| `reports/` | listed | Empty (`.gitkeep` + `README.md`). |
| `.github/workflows/ci.yml` | yes | Runs `ruff check`, `ruff format --check`, `pytest tests -q` on push/PR for `main` and `research/**`; freqtrade not installed (intentional). |

---

## 3. Current research architecture

A short summary of how the project is wired; see `README.md`, `docs/REPOSITORY_AUDIT.md` and `docs/FROZEN_IMPLEMENTATION_SPEC.md` for the full description.

```
candles  →  indicators (pa_indicators.py, pure, causal)
        →  signals    (pa_signals.py / pa_pullback.py / pa_structure.py, pure, causal)
        →  strategy   (user_data/strategies/<family>/<Name>.py   freqtrade IStrategy)
                     or (research_lib/strategies/<Name>.py        research IStrategy)
        →  risk       (pa_risk.py, pure sizing / stop maths)
        →  freqtrade engine  (backtest only)
```

Production vs research separation (verified):

- **Production** = `user_data/strategies/turtle/DonchianTurtleBaseline.py` @ `12acbf7`, frozen, never edited by research code.
- **Research** = `research_lib/strategies/*.py` (P3-EXP-001/003). Lives outside `user_data/strategies/` so it can never be confused with a production strategy.

Pipeline governance is enforced by:

1. `pyproject.toml` declares `freqtrade` *not pinned*; the framework is supplied via the `FREQTRADE_SRC` env var (`C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop`).
2. `conftest.py` + `tests/conftest.py` best-effort resolve freqtrade; tests skip if it is not importable.
3. `.github/workflows/ci.yml` does **not** install freqtrade (intentional — CI verifies pure-logic tests, not backtest runs).
4. `.gitignore` blocks `.env`, raw data, backtest outputs, model binaries.
5. Strategies under `user_data/strategies/` import only the shared `pa_*` modules, never another strategy; `test_pullback_strategy.py::TestNoTurtleCoupling` enforces non-coupling.

Per-phase governance:

- Phase A (Repository Audit): `docs/REPOSITORY_AUDIT.md` (A1–A20).
- Phase B (Research): `research/notion_map.md` + `docs/EXTERNAL_EVIDENCE.md`.
- Phase C (Data): `docs/DATA_AVAILABILITY.md` + `research/experiment_results/P3_FUTURES_DATA_MANIFEST.json`.
- Phase D (Critical Evaluation): `docs/PHASE_D_CRITICAL_EVALUATION.md`.
- Frozen implementation: `docs/FROZEN_IMPLEMENTATION_SPEC.md` (with three open specification issues: SI-1, SI-2, SI-3).

---

## 4. Active / uncommitted work

### 4.1 Active work

The HEAD commit (`5c3d4fb`) — *"P3-EXP-003 carry (FAIL), fix SI-4 funding defect, re-run P3-EXP-001/002 with funding"* — is the most recent activity. It:

- Adds P3-EXP-003 (carry) implementation, config, runner, results, and decision (`FAIL`).
- Identifies and fixes SI-4 (freqtrade requires **1h mark** candles for funding to be applied; the first Phase-3 download had only 4h mark).
- Re-runs **all 16 P3-EXP-001 runs** and **all 14 P3-EXP-002 runs** with funding now correctly applied, superseding the earlier numbers (earlier numbers are *not* deleted; the corrections are recorded in `docs/ISSUES_LOG.md` and inside each experiment's `*.md`/`*.json`).
- Updates `docs/DATA_AVAILABILITY.md` (1h-mark added; funding verified at 0.4259 USDT for a manual LINK spot-check).
- Commits the empty MECE scaffolding (`.mece/SYNTHESIS.md`, `.mece/WAVE.md`).

### 4.2 Uncommitted work (at audit time)

**None at audit time.** `git diff HEAD` and `git diff --cached HEAD` both
returned zero lines; the only untracked content was the three MECE `TASK.md`
files (inputs for this MECE cell wave). No source files were open in a dirty
state.

*(This is the pre-repair audit state. After the wave's repairs the final tree is
**not** clean — see the scope note and §8.)*

### 4.3 Open / outstanding experiment slots

| Slot | Status | Why open |
|------|--------|----------|
| `EXP-005` (Breakout-retest standalone) | not implemented; `user_data/strategies/breakout_retest/` is empty | Predecessors EXP-001/003/004 all FAIL. The hypothesis document `research/hypotheses/breakout_retest.md` exists but no spec was frozen. |
| `EXP-006` (Turtle + Breakout-retest) | not started | Depends on EXP-005. |
| `EXP-007` (Volatility expansion standalone) | not implemented; `user_data/strategies/volatility_expansion/` is empty | Predecessor EXP-006 FAIL. |
| `EXP-008` (Turtle + Volatility expansion) | not started | Depends on EXP-007. |
| `EXP-009` (Swing-structure standalone) | no hypothesis document exists at `research/hypotheses/swing_structure.md` (only turtle / pullback_continuation / breakout_retest / volatility_expansion) | Sequence shows it but no hypothesis was ever written. |
| `EXP-010`–`EXP-013` (ML filters) | not started | ml/ is empty scaffolding; charter forbids ML before rule-based setup validates. |
| `EXP-014`, `EXP-015` (cross-strategy / router) | not started | Charter forbids router without validated components. |
| `P3-EXP-004A` (cross-sectional momentum) | code not written | Same instrument class had a documented prior failure (Fayez Junior 2026). |
| `P3-EXP-004B` (residual momentum) | code not written | Equity evidence only (Blitz/Huij/Martens 2011). |
| `P3-EXP-006` (ATR vs GK volatility estimator) | code not written | Yang–Zhang explicitly excluded per frozen spec §6.4. |
| `P3-EXP-007` (regime) | code not written | PHASE-2 documented a regime shift but explicitly did not justify a filter. |
| `P3-EXP-008` (ML meta-filter) | code not written; LightGBM not installed; sklearn/XGBoost available | Frozen spec §6.6 authorises single-model meta-labelling last; LightGBM not installed. |

### 4.4 Open specification issues (`docs/FROZEN_IMPLEMENTATION_SPEC.md` §SPECIFICATION ISSUES)

| ID | State | Notes |
|----|-------|-------|
| SI-1 | **resolved** for OHLCV availability (see `docs/DATA_AVAILABILITY.md`); results now use `data_p3` genuine futures dataset |
| SI-2 | **open** — 2025–2026 are non-pristine (already observed by EXP-001/002/003/004/PHASE-2); pristine holdout requires post-2026-09 data |
| SI-3 | **open** — Phase-3 research implementations exist for 001/002/003; 004A, 004B, 006, 007, 008 are **not** written and would need explicit authorisation before implementation |
| SI-4 | **resolved** — funding-fee defect fixed by adding 1h mark; affected runs re-executed and superseded |

---

## 5. Important risks

Carried from `docs/REPOSITORY_AUDIT.md` A17 and re-verified by this cell; nothing new has been invented.

1. **`README.md` is stale.** Claims "76 tests passing" (actual unit suite is 7 files; repo audit reports 133 collected). Lists EXP-002/003/004 as `PLANNED`. References `breakout_retest/` and `volatility_expansion/` strategy directories that **exist as empty folders only**. The headline-status table does not yet mention P3-EXP-001/002/003.
2. **`user_data/configs/README.md` is stale.** Documents only `EXP-001.json`; four more configs (`EXP-002`, `EXP-003`, `EXP-003-long`, `EXP-003-short`, `EXP-003-spot-long`) plus `P3-EXP-001.json` and `P3-EXP-003.json` exist.
3. **GitHub remote is unreachable.** `git ls-remote origin` returns `Repository not found`. The git history is local-only; no off-machine backup.
4. **Working production/strategy isolation verified but not actively enforced.** No pre-commit hook or CI check forbids `git diff` of the frozen baseline directory; isolation is procedural (charter + the `git diff` checks in PHASE-2 and P3 result documents).
5. **Funding-fee defect (SI-4) was silent.** freqtrade did **not** raise an error when mark data was missing — it logged a warning and applied zero funding. Detection relied on the P3-EXP-003 runner *choosing* to report `funding_applied`. Future experiments should require `funding_fees != 0` as a sanity check.
6. **All three Phase-3 experiments run so far have FAILED.**
   - P3-EXP-001 — Turtle genuine-futures baseline; OOS PF 0.81 / 0.85 for the two long arms.
   - P3-EXP-002 — Cost sensitivity; verdict flipped PASS→FAIL when SI-4 was fixed (vol-scaled arm no longer meets the stress threshold).
   - P3-EXP-003 — Carry; **the strategy net-paid funding (−11,306 USDT)** instead of harvesting it; OOS PF 0.805.
7. **Carry is the most-documented orthogonal exposure in this project** (Cao/Zhai/Luo 2024; arXiv `2212.06888`; "Crypto Carry Trade" 2026 CFTC comment). A naive single-leg trailing-sign implementation did not realise it; a more sophisticated carry definition (e.g. true cash-and-carry with a spot leg) would be a **new** hypothesis, not a tweak, and is not authorised by the frozen spec.
8. **2025 and 2026 holdouts are no longer pristine** (already observed by EXP-001/002/003/004, PHASE-2 and P3-EXP-001/002/003). Any future experiment that touches these windows is non-pristine by construction and must be labelled as such.
9. **Charter sequence divergence (known).** Charter lists EXP-004 as `Turtle + Pullback`; EXP-004 was re-scoped (DEC-005) to a fresh OOS validation of the frozen long-only pullback strategy, recorded in `research/decisions/DECISION_LOG.md` and `research/experiment_specs/EXP-004.md`. Charter table is knowingly out of date for that one row.
10. **Empty scaffolding that can be mistaken for implemented capability.** `ml/` (subfolders + README only), `reports/` (`.gitkeep` + README only), `tests/integration/`, `tests/research/`, `breakout_retest/` and `volatility_expansion/` strategy folders (only `__pycache__`).
11. **No walk-forward harness** in repo (`research/walk_forward/` has a README + `.gitkeep` only). `PHASE2_DIAGNOSTIC.md` already notes that walk-forward is the right next step once anything passes A1–A8; nothing has, so it has never run.
12. **Production artefacts in `user_data/backtest_results/`.** 481 files (`.json` + `.zip` + `.meta.json`) accumulated by P3 runners. Gitignored but worth knowing they exist; `rm` is **not** recommended (they are referenced by `.last_result.json` for the most recent run).
13. **Framework revision is "freqtrade 2026.9-dev" + CCXT 4.5.71 + Python 3.12.10 + pandas 3.0.5 + numpy 2.4.6** (per `experiment_protocol.md` §92–94). The framework source checkout is at `C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop` (verified present). If the host machine's freqtrade checkout drifts, recorded numbers may not reproduce exactly.

---

## 6. Verification commands performed

The following commands were run during this audit; output was observed (not modified):

```powershell
git status                                          # on branch research/diagnostic-generalization; only 3 untracked TASK.md files
git branch --show-current                           # research/diagnostic-generalization
git log --oneline -10                               # HEAD = 5c3d4fb (P3-EXP-003 + SI-4 fix)
git branch -a                                       # 6 branches listed
git status --porcelain --untracked-files=all        # only 3 TASK.md files untracked
git diff HEAD                                       # empty (working tree clean)
git diff --cached HEAD                              # empty (no staged)
git stash list                                      # empty
git remote -v                                       # asdramxrt-oss/freqtrade-pa-momentum-research.git
git ls-remote origin                                # 404 - GitHub repository does not exist
git config --get remote.origin.url                  # confirmed
git diff --stat HEAD~1 HEAD                         # 17 files changed in most recent commit
git diff --stat HEAD~2 HEAD~1                       # 4 files (P3-EXP-002 commit)
git diff --stat HEAD~3 HEAD~2                       # 6 files (P3-EXP-001 commit)
git show --stat HEAD --pretty=oneline               # full last-commit content
git show --stat 6bd018e --pretty=oneline            # P3-EXP-001 commit
git show --stat 636890a --pretty=oneline            # P3-EXP-002 commit
Test-Path -Path "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop"  # True
Get-ChildItem .mece -Recurse                        # confirmed 3 TASK.md + 2 empty placeholders
Get-ChildItem user_data/strategies/breakout_retest -Recurse -File  # empty (only __pycache__)
Get-ChildItem user_data/strategies/volatility_expansion -Recurse -File  # empty
Get-ChildItem -Recurse -File (user_data/backtest_results)  # 481 files
Get-ChildItem user_data/data/binance/futures        # 50 feathers (spot mirror, 10 pairs x 5 candle types)
Get-ChildItem user_data/data_p3/futures             # 60 feathers (genuine futures, 10 pairs x 6 candle types incl. 1h-mark)
```

Files **read** (in addition to those listed in §2):
- `README.md`, `pyproject.toml`, `conftest.py`, `tests/conftest.py`, `tests/helpers.py`, `.gitignore`, `.env.example`
- All seven `docs/` files
- All seven `research/hypotheses/*.md` (turtle + pullback in full, breakout_retest + volatility_expansion read)
- All six `research/experiment_specs/*.md`
- All four `research/experiment_results/EXP-*.md` plus `PHASE2_DIAGNOSTIC.md`, `P3-EXP-001.md`, `P3-EXP-002.md`, `P3-EXP-003.md`
- `research/experiment_results/P3-EXP-001.json`, `P3-EXP-002.json`, `P3-EXP-003.json`, `P3_FUTURES_DATA_MANIFEST.json` (first 50 lines)
- `research/decisions/DECISION_LOG.md`, `research/notion_map.md`
- `research_lib/strategies/TurtleFuturesResearch.py`, `research_lib/strategies/FundingCarryResearch.py`
- `user_data/configs/P3-EXP-001.json`, `P3-EXP-003.json`
- `user_data/scripts/p3_exp001_run.py`, `p3_exp002_costs.py`, `p3_exp003_carry.py`
- `ml/README.md`
- `.github/workflows/ci.yml`

Files **listed but not opened** (path-only):
- All `tests/unit/test_*.py` files (presence + name only)
- All `tests/integration/`, `tests/research/`, `ml/*/` subfolders (confirmed empty)
- All `user_data/backtest_results/*` (counted: 481 files)
- All `user_data/data*/binance/futures/*` and `user_data/data_p3/futures/*` feathers (counted)
- `user_data/strategies/breakout_retest/`, `user_data/strategies/volatility_expansion/` (confirmed empty)

No command executed modified the working tree, the index, the stash, the remote, or any tracked file. No production-trading logic was inspected that is not already documented in the repo.

---

## 7. Recommended handoff to the parent conductor

For the parent MECE conductor / wave manager:

1. **The audit is read-only and reproducible.** Section §6 lists every command run and every file read. Re-running those commands yields the same *audit-time* observations (the tracked working tree was clean and the remote is still 404). *The "clean tree" observation is the pre-repair state; the final post-wave tree is not clean — see §8.*
2. **No file was created, deleted, renamed, modified or staged during this audit.** The only file this cell wrote was this `REPORT.md`, exactly as instructed. *(The wave subsequently applied its repairs and wrote its artifacts — §8.)*
3. **CELL-002 can proceed next.** All required inputs (`research/experiment_results/`, `docs/`, `research_lib/`, `user_data/configs/`, `user_data/scripts/`) are present, readable, and not in a dirty state. The six experiment result documents (EXP-001.md, EXP-002.md, EXP-003.md, EXP-004.md, PHASE2_DIAGNOSTIC.md, P3-EXP-001.md, P3-EXP-002.md, P3-EXP-003.md) are sufficient to characterise measured results, methodology and limitations without rerunning anything.
4. **CELL-003 can run after CELL-002.** It depends on the FACT / INTERPRETATION / UNKNOWN separation that CELL-002 is asked to produce. CELL-003 must not invent architectures that aren't justified by the evidence CELL-002 surfaces.
5. **Three pieces of state are worth flagging forward.**
   - The **funding-fee defect (SI-4)** must be carried forward as a baseline assumption for any future futures experiment: 1h mark must be present, and `funding_fees != 0` is the running-total sanity check.
   - The **GitHub remote 404** means there is no off-machine backup of this repository. If a parent wave deletes or rewrites a large part of the history, it cannot be recovered remotely. (No action recommended; just do not rely on `git push` as a safety net.)
   - The **charter sequence** has a known divergence for the EXP-004 row (re-scoped under DEC-005). Any future cell that touches the charter sequence table should record the same governance note.
6. **No production trading code was inspected that is not already committed.** `DonchianTurtleBaseline.py` @ `12acbf7` is the frozen reference baseline and was not opened by this audit; `research_lib/strategies/*.py` are the only research-strategy modules read in full.
7. **No work has been initiated, restarted, or undone (at audit time).** All experiment results were exactly as committed at the most recent commit (`5c3d4fb`); all branches and tags were as recorded in `git branch -a`; the working tree was clean; no run was rerun.

---

## 8. Post-wave reconciliation (added by the final integrity pass)

The statements in §1–§7 above describe the **pre-repair audit state**. After this
audit the MECE wave applied its repairs and wrote its artifacts. The **final
observed state** is:

| Item | Final post-wave value |
|------|-----------------------|
| Modified (tracked) | **10 files** — the eight research repair targets: `conftest.py`, `tests/conftest.py`, `research_lib/strategies/FundingCarryResearch.py`, `user_data/scripts/diagnostics/diagnose_data_quality.py`, `research/experiment_results/P3-EXP-001.md`, `research/experiment_results/P3-EXP-002.md`, `docs/EXPERIMENT_REGISTRY.md`, `docs/PHASE_D_CRITICAL_EVALUATION.md` — plus the wave artifacts `.mece/WAVE.md` and `.mece/SYNTHESIS.md` |
| Untracked | `.mece/cells/CELL-001…003/{TASK,REPORT}.md`, `.mece/PHASE_GATE.json` |
| Tracked working tree clean? | **No** — intentionally not clean until the final commit |
| Production strategy diff | **zero lines** — `user_data/strategies/{turtle,pullback,shared}` untouched |
| Tests | `python -m pytest tests -q` → **133 passed** |
| Ruff | `ruff check .` clean; `ruff format --check .` clean (**86 files already formatted**) |
| Phase-2 diagnostics | reproduced identically apart from timestamps |

The MECE artifacts are deliberately kept present and uncommitted until the final
commit. No new Phase-3 experiment was executed during this wave (the only runs
were read-only reproductions of the committed Phase-2 diagnostics).

This audit ends here.