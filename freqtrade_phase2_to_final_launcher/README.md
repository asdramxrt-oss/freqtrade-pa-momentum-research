# Freqtrade Phase 2 → Final Phase Automation Package

## What this package does

This is a single Windows launcher layer for the MECE research workspace.
It automatically detects the current phase from `.mece/PHASE_GATE.json`
and invokes the existing `automation.bridge` safety pipeline.

The same launcher can therefore continue from Phase 2 into Phase 3 and
later phases as the repository's own governance state advances.

## One-click usage

1. Extract this ZIP.
2. If the package is outside the research repo, place the extracted folder
   beside the repo using this layout:

   <parent>\
       all_phases_launcher_package\
       freqtrade-pa-momentum-research\

3. Or copy the package files directly into:

   C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research

4. Double-click `RUN_ALL_PHASES.bat`.

For continuous operation, double-click:

`RUN_CONTINUOUS_ALL_PHASES.bat`

## Windows automatic startup

Double-click:

`INSTALL_ALL_PHASES_TASK.bat`

This creates an ONLOGON scheduled task.

To remove it:

`UNINSTALL_ALL_PHASES_TASK.bat`

## Safety model

This package is deliberately gate-driven.

It calls:

    python -m automation.bridge --json

It does NOT automatically add:

    --force
    --include-experiments
    --run-analysis
    --with-crew
    --with-opencode

Those are intentionally left as explicit operator/governance-controlled
capabilities.

A closed MECE gate is never bypassed. The controller may run safe
validation/report/next-task work that the bridge itself permits, but it
does not turn a closed experiment gate into an open one.

## Phase progression

The controller does not hard-code "Phase 3", "Phase 4", etc. as executable
commands. It reads the current MECE phase and lets the repository's
governance determine what is permitted.

This avoids a dangerous failure mode where a script assumes a phase is ready
just because a calendar/time threshold was reached.

Expected flow:

    Phase 2 gate/state
        ↓
    safe bridge pass
        ↓
    reports + NEXT_TASK
        ↓
    human/governance phase transition
        ↓
    controller sees new phase
        ↓
    next permitted bridge pass
        ↓
    repeat until final/completed/blocked

## Important current-state note

Your current repository has a closed Phase 2 experiment gate. Therefore this
package does not magically execute the next experiments today. It provides
the reusable Phase-2-to-final controller infrastructure while preserving the
existing fail-closed governance.

When the MECE state legitimately advances to a later phase and its gate
allows the required work, the same controller can continue without requiring
a new launcher for every phase.

## Recovery

The controller retries transient bridge failures up to two times.

It stops on:
- governance stop code,
- repeated failures,
- missing repository,
- missing MECE gate,
- missing automation bridge.

It never calls `--force`.

## Scope

This package is a launcher/controller layer. The research logic remains in
the repository. It does not rewrite production strategies, silently alter
experiment results, or invent phase completion.
