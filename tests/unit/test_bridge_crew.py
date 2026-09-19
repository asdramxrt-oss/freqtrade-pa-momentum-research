"""Unit tests for the optional CrewAI orchestration layer."""

from __future__ import annotations

import pytest

from automation import crew

pytestmark = pytest.mark.bridge


class _FakeBuild:
    """Minimal stand-in for :class:`crew.CrewBuild`."""

    crew = "FAKE_CREW"


def test_no_execution_tool_names() -> None:
    crew.assert_no_execution_tools()
    for name in crew.tool_names():
        lowered = name.lower()
        for token in crew.FORBIDDEN_TOOL_TOKENS:
            assert token not in lowered


def test_build_crew_requires_crewai() -> None:
    if not crew.CREWAI_AVAILABLE:
        with pytest.raises(RuntimeError):
            crew.build_crew()
        return
    build = crew.build_crew()
    assert build.tool_names
    assert build.crew is not None


def test_run_crew_skips_without_crewai(monkeypatch) -> None:
    monkeypatch.setattr(crew, "CREWAI_AVAILABLE", False)
    result = crew.run_crew(None)
    assert result.skipped is True
    assert result.executed is False
    assert result.output == ""


def test_run_crew_executes_with_injected_hooks(monkeypatch) -> None:
    monkeypatch.setattr(crew, "CREWAI_AVAILABLE", True)
    seen: dict[str, object] = {}

    def builder(cfg):
        seen["cfg"] = cfg
        return _FakeBuild()

    def kickoff(actual_crew):
        seen["crew"] = actual_crew
        return "kicked"

    result = crew.run_crew(None, builder=builder, kickoff=kickoff)
    assert result.executed is True
    assert result.skipped is False
    assert result.output == "kicked"
    assert seen["crew"] == "FAKE_CREW"
