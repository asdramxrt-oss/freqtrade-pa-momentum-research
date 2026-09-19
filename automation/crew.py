"""CrewAI orchestration layer for the bridge.

CrewAI is an optional dependency (the ``bridge`` extra). Importing this module
without CrewAI installed is safe; :func:`build_crew` raises only when called.

Every tool is read-only with respect to recorded results and production code.
There is deliberately no tool that can place an order, move funds, or start a
new experiment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from automation import next_task as next_task_mod
from automation import report as report_mod
from automation import validation as validation_mod
from automation.config import BridgeConfig, load_config
from automation.gate import load_gate

try:
    from crewai import Agent, Crew, Process, Task
    from crewai.tools import tool

    CREWAI_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the extra
    Agent = None  # type: ignore[assignment,misc]
    Crew = None  # type: ignore[assignment,misc]
    Process = None  # type: ignore[assignment,misc]
    Task = None  # type: ignore[assignment,misc]
    tool = None  # type: ignore[assignment]

    CREWAI_AVAILABLE = False

# Tool names must never imply an execution capability.
FORBIDDEN_TOOL_TOKENS = ("order", "trade", "withdraw", "transfer", "live", "fund")


def _tool_functions() -> list[Any]:
    """
    Return the bridge's CrewAI-callable tools (as plain functions).

    :return: List of functions.
    """

    def bridge_gate_status() -> str:
        """Return the current phase-gate state."""
        gate = load_gate()
        state = gate.as_dict()
        return (
            f"phase={state['phase']}; "
            f"allow_new_experiments={state['allow_new_experiments']}; "
            f"stop_after_phase_completion={state['stop_after_phase_completion']}"
        )

    def bridge_validate() -> str:
        """Run the read-only validation suite and return a summary."""
        result = validation_mod.run_validation()
        return "; ".join(
            f"{check.name}={'PASS' if check.ok else 'FAIL'}" for check in result.checks
        )

    def bridge_report(run_id: str = "phase2_bridge") -> str:
        """Write the deterministic REPORT.md derived from recorded artifacts."""
        cfg = load_config()
        gate = load_gate()
        return str(report_mod.build_report(cfg, gate, run_id))

    def bridge_propose_next_task(run_id: str = "phase2_bridge") -> str:
        """Write the next-task PROPOSAL only; it is never executed."""
        cfg = load_config()
        gate = load_gate()
        return str(next_task_mod.propose_next_task(cfg, gate, run_id).path)

    return [bridge_gate_status, bridge_validate, bridge_report, bridge_propose_next_task]


def tool_names() -> list[str]:
    """
    Return the bridge tool names.

    :return: List of function names.
    """
    return [function.__name__ for function in _tool_functions()]


def assert_no_execution_tools() -> None:
    """
    Assert that no tool name implies an execution capability.

    :raises AssertionError: When a forbidden token appears in a tool name.
    """
    for name in tool_names():
        lowered = name.lower()
        for token in FORBIDDEN_TOOL_TOKENS:
            if token in lowered:
                raise AssertionError(f"forbidden execution token {token!r} in tool {name!r}")


@dataclass
class CrewBuild:
    """Built CrewAI objects plus metadata."""

    crew: Any
    agent: Any
    task: Any
    tools: list[Any]
    tool_names: list[str]


@dataclass
class CrewRunResult:
    """Outcome of a CrewAI orchestration run."""

    executed: bool
    skipped: bool
    reason: str
    output: str = ""


def run_crew(
    cfg: BridgeConfig | None = None,
    *,
    builder: Any = None,
    kickoff: Any = None,
) -> CrewRunResult:
    """
    Run the CrewAI orchestration stage of the one-click bridge.

    Degrades gracefully: when CrewAI is not installed the step is skipped, so
    the deterministic pipeline still works. The ``builder``/``kickoff`` hooks
    exist so tests can exercise the wiring without an LLM or the extra.

    :param cfg: Optional bridge configuration.
    :param builder: Optional callable returning a :class:`CrewBuild`.
    :param kickoff: Optional callable taking the crew and returning output.
    :return: Run result.
    """
    if not CREWAI_AVAILABLE:
        return CrewRunResult(
            executed=False,
            skipped=True,
            reason="crewai is not installed; install the optional 'bridge' extra",
        )
    build = builder or build_crew
    built = build(cfg)
    kick = kickoff or (lambda crew: crew.kickoff())
    output = kick(built.crew)
    return CrewRunResult(
        executed=True,
        skipped=False,
        reason="crew executed",
        output="" if output is None else str(output),
    )


def build_crew(cfg: BridgeConfig | None = None) -> CrewBuild:
    """
    Build the single-agent bridge crew.

    :param cfg: Optional bridge configuration (resolved when omitted).
    :return: Built crew bundle.
    :raises RuntimeError: When CrewAI is not installed.
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError(
            "crewai is not installed; install the optional 'bridge' extra "
            "(pip install -e .[bridge]) or run the bridge without the crew step"
        )
    assert_no_execution_tools()
    tools = [tool(function) for function in _tool_functions()]
    agent = Agent(
        role="Phase-2 research bridge orchestrator",
        goal=(
            "Chain OpenCode advisories, local Freqtrade analysis and validation "
            "into a reproducible REPORT.md and a next-task proposal, without ever "
            "executing a new experiment or touching frozen production code."
        ),
        backstory=(
            "A research-only automation coordinator for the freqtrade PA momentum "
            "programme. It treats .mece/PHASE_GATE.json as authoritative, keeps "
            "production strategies frozen, and proposes rather than executes."
        ),
        tools=tools,
        allow_delegation=False,
        verbose=False,
    )
    task = Task(
        description=(
            "Run the bridge for the current phase: inspect the gate, validate the "
            "repository state, produce the derived REPORT.md, and write the "
            "next-task PROPOSAL to .mece/NEXT_TASK.md. Never execute the proposal."
        ),
        expected_output=(
            "A validation summary, a written reports/<run_id>_REPORT.md, and a "
            "written .mece/NEXT_TASK.md marked PROPOSAL ONLY."
        ),
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    return CrewBuild(
        crew=crew,
        agent=agent,
        task=task,
        tools=tools,
        tool_names=tool_names(),
    )
