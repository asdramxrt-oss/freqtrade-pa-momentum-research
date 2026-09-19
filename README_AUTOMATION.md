# ChatGPT + CrewAI + OpenCode automation

This package adds an orchestration layer around the existing Freqtrade research project.

Roles:
- ChatGPT: parent/conductor and governance-aware reviewer.
- CrewAI: research task orchestration.
- OpenCode: repository coding/execution muscle.
- Windows controller: unattended scheduling and state handoff.

Safety:
- Never edits `.mece/PHASE_GATE.json`.
- Never treats a closed gate as authorization.
- Never enables live trading.
- Never auto-promotes a strategy.
- Never performs parameter search unless the repository's frozen methodology explicitly authorizes it.
- Stops at governance boundaries.
- Missing tools/dependencies cause a recorded WAIT/BLOCKED state, not a bypass.

The package is intentionally fail-closed. It does not manufacture authorization for P3-EXP-004A.
