"""Tests for orchestrator/skill_loader.py."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from orchestrator.skill_loader import (
    SkillEntry,
    build_orchestrator_prompt,
    build_skill_files,
    build_subagents,
    load_skill_registry,
)


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with test skills."""
    # Echo skill (inline)
    echo_dir = tmp_path / "echo"
    echo_dir.mkdir()
    (echo_dir / "SKILL.md").write_text(
        """\
---
name: echo
description: Echoes back the user's input.
version: "1.0"
metadata:
  dispatch: inline
  tools_allowed: []
---

# Echo Skill

Repeat the user's input back to them.
"""
    )

    # Research skill (subagent)
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    (research_dir / "SKILL.md").write_text(
        """\
---
name: research-analyst
description: Gathers and synthesizes information from web sources.
version: "1.0"
metadata:
  dispatch: subagent
  model: "anthropic:claude-opus-4-6"
  tools_allowed:
    - web_search
    - fetch_url
  output_schema:
    findings: "list[str]"
---

# Research Analyst

## Purpose
You are a research analyst.

## Last message contract
Your final message is the only output the orchestrator will see.
"""
    )

    # Invalid skill (missing name) — should be skipped
    invalid_dir = tmp_path / "invalid"
    invalid_dir.mkdir()
    (invalid_dir / "SKILL.md").write_text(
        """\
---
description: Missing name field.
---

# Invalid
"""
    )

    # Reference files for research skill
    refs_dir = research_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "rubric.md").write_text("# Source Quality Rubric\n\n- Check dates\n")

    return tmp_path


def test_load_skill_registry(skills_dir: Path) -> None:
    registry = load_skill_registry(str(skills_dir))

    # Invalid skill should be filtered out
    assert len(registry) == 2
    names = [s.name for s in registry]
    assert "echo" in names
    assert "research-analyst" in names


def test_load_skill_registry_empty_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    registry = load_skill_registry(str(empty))
    assert registry == []


def test_load_skill_registry_nonexistent() -> None:
    registry = load_skill_registry("/nonexistent/path")
    assert registry == []


def test_skill_entry_metadata(skills_dir: Path) -> None:
    registry = load_skill_registry(str(skills_dir))
    research = [s for s in registry if s.name == "research-analyst"][0]

    assert research.metadata["dispatch"] == "subagent"
    assert research.metadata["tools_allowed"] == ["web_search", "fetch_url"]
    assert research.metadata["model"] == "anthropic:claude-opus-4-6"


def test_skill_entry_full_body(skills_dir: Path) -> None:
    registry = load_skill_registry(str(skills_dir))
    echo = [s for s in registry if s.name == "echo"][0]

    assert "# Echo Skill" in echo.full_body
    assert "Repeat the user's input" in echo.full_body


def test_build_orchestrator_prompt(skills_dir: Path) -> None:
    registry = load_skill_registry(str(skills_dir))
    prompt = build_orchestrator_prompt(registry)

    assert "## Available Skills" in prompt
    assert "echo" in prompt
    assert "research-analyst" in prompt
    assert "inline" in prompt
    assert "subagent" in prompt
    assert "web_search" in prompt


def test_build_orchestrator_prompt_empty() -> None:
    prompt = build_orchestrator_prompt([])
    assert prompt == ""


def test_build_skill_files(skills_dir: Path) -> None:
    files = build_skill_files(str(skills_dir))

    # Should include SKILL.md files
    skill_paths = [p for p in files if p.endswith("SKILL.md")]
    assert len(skill_paths) >= 2

    # Should include reference files
    ref_paths = [p for p in files if "rubric.md" in p]
    assert len(ref_paths) == 1
    assert "Source Quality Rubric" in files[ref_paths[0]]


def test_build_subagents(skills_dir: Path) -> None:
    registry = load_skill_registry(str(skills_dir))
    subagents = build_subagents(registry)

    # Only subagent-dispatch skills
    assert len(subagents) == 1
    sa = subagents[0]
    assert sa["name"] == "research-analyst"
    assert sa["description"] == "Gathers and synthesizes information from web sources."
    assert "# Research Analyst" in sa["prompt"]
    assert sa["tools"] == ["web_search", "fetch_url"]


def test_build_subagents_no_tools(skills_dir: Path) -> None:
    registry = load_skill_registry(str(skills_dir))
    # Echo is inline, not subagent — should not appear
    subagents = build_subagents(registry)
    names = [sa["name"] for sa in subagents]
    assert "echo" not in names


def test_build_subagents_empty() -> None:
    subagents = build_subagents([])
    assert subagents == []
