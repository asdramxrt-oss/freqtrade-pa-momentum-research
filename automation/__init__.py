"""Phase-2 automation bridge (orchestration only, research-safe).

The bridge chains CrewAI (orchestration) -> OpenCode (analysis/advisory) ->
local Python/Freqtrade analysis -> validation -> REPORT.md -> next-task
proposal.

It deliberately contains **no** strategy logic, no parameter selection and no
live-trading capability. Every step is read-only with respect to the frozen
production strategy subtrees and the recorded experiment results, and the
``.mece/PHASE_GATE.json`` gate is authoritative.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
