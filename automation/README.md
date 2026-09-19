# Automation bridge (Phase 2)

One-click orchestration for the Phase-2 research record:

```
gate -> crew (opt-in) -> analysis (opt-in) -> OpenCode (opt-in) -> validation
     -> REPORT.md -> next-task proposal
```

It is **orchestration only**. It contains no strategy logic, selects no
parameter, and cannot trade. It shells out to the existing runners in
`user_data/scripts/` and never re-implements their metrics.

## The CrewAI stage

`--with-crew` (or `run_bridge.ps1 -WithCrew`) runs the CrewAI orchestrator in
`automation/crew.py`. `crew.run_crew()` builds the crew and calls `kickoff()`;
its tools are read-only (`bridge_gate_status`, `bridge_validate`,
`bridge_report`, `bridge_propose_next_task`) and there is no order/trade tool.

CrewAI is an **optional** dependency (the `bridge` extra, unpinned). When it is
not installed the stage is reported as `skipped` and the deterministic pipeline
still runs to completion. Crew failures abort only when the stage was explicitly
requested.

## Run-id safety

`run_id` is validated by `config.sanitize_run_id` (`[A-Za-z0-9._-]{1,128}`,
rejecting `.`/`..`) before it is used in `reports/<run_id>_REPORT.md` or an
OpenCode transcript name, so it cannot traverse out of those directories.

## Safety contract

1. **Gate is authoritative.** `.mece/PHASE_GATE.json` is read on every run. A
   missing, malformed or partially-typed gate is a hard error (fail-closed).
   Experiment-class runners are refused unless `allow_new_experiments` is true
   *and* `stop_after_phase_completion` is false.
2. **Production is frozen.** `user_data/strategies/{turtle,pullback,shared}` must
   diff to zero lines; otherwise validation fails and no report is written.
3. **Recorded results are immutable.** The bridge snapshots
   `research/experiment_results/*.{json,md}` around the analysis and OpenCode
   steps; if any *substantive* content changes, the run aborts. JSON is
   canonicalised with the `generated_utc` bookkeeping field removed, so a
   faithful diagnostic reproduction (same numbers, new timestamp) passes while
   any changed metric fails. The diagnostic scripts are still opt-in
   (`--run-analysis`).
4. **Proposal, not execution.** `.mece/NEXT_TASK.md` is always marked
   `PROPOSAL ONLY`; `executed` is always false.
5. **No shell, no auto-approval.** Subprocesses are invoked with argv lists and
   `shell=False`-style semantics; OpenCode's permission auto-approval flag is
   never passed.

## One-click

```powershell
# validate, write reports/phase2_bridge_REPORT.md and .mece/NEXT_TASK.md
./run_bridge.ps1

# include the real diagnostic analysis and an OpenCode advisory
./run_bridge.ps1 -RunAnalysis -WithOpenCode -Json

# print the plan only
./run_bridge.ps1 -DryRun
```

## Module map

| Module | Responsibility |
|--------|----------------|
| `config.py` | Path + interpreter + OpenCode resolution (no environment mutation) |
| `gate.py` | Fail-closed reader for `.mece/PHASE_GATE.json` |
| `runners.py` | Wrappers over `user_data/scripts/**` (diagnostic vs experiment class) |
| `opencode_client.py` | Non-interactive OpenCode invocation + transcript |
| `validation.py` | Production zero-diff, gate, artifact consistency, safety scan |
| `report.py` | Deterministic derived `REPORT.md` (no timestamps) |
| `next_task.py` | Reads `.mece`/decision/registry state; writes a proposal only |
| `crew.py` | Optional CrewAI orchestration (`run_crew`, the `bridge` extra) |
| `bridge.py` | CLI chaining the steps (crew → analysis → OpenCode → validation → report → next-task) |

## Interpreter

Use `PA_BRIDGE_PYTHON` (or `run_bridge.ps1`, which prefers `py -3.12`). The bare
`python` on this machine can resolve to an unrelated CrewAI virtualenv that
lacks pandas/ruff.

## Tests

Bridge tests are marked `bridge`:

```powershell
python -m pytest tests -q -m bridge
```
