"""Skill loader with progressive disclosure.

Stage 1 — Registry: Read only YAML frontmatter at startup.
Stage 2 — Activation: Full body read at runtime via read_file tool.

Skill files live at skills/<name>/SKILL.md with YAML frontmatter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frontmatter


@dataclass
class SkillEntry:
    """A loaded skill's metadata (frontmatter only) plus filesystem path."""

    name: str
    description: str
    version: str
    metadata: dict[str, Any]
    file_path: str  # relative path from project root, e.g. "skills/research/SKILL.md"
    full_body: str = ""  # populated only when full file is read


def load_skill_registry(skills_dir: str = "skills") -> list[SkillEntry]:
    """Load frontmatter from all skills/<name>/SKILL.md files.

    Returns a list of SkillEntry with metadata only (no full body).
    This is Stage 1 of progressive disclosure.
    """
    registry: list[SkillEntry] = []
    skills_path = Path(skills_dir)

    if not skills_path.exists():
        return registry

    for skill_dir in sorted(skills_path.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue

        post = frontmatter.load(str(skill_file))
        fm = post.metadata

        if not fm.get("name") or not fm.get("description"):
            continue

        entry = SkillEntry(
            name=fm["name"],
            description=fm.get("description", ""),
            version=fm.get("version", "0.1"),
            metadata=fm.get("metadata", {}),
            file_path=str(skill_file),
            full_body=post.content,
        )
        registry.append(entry)

    return registry


def build_orchestrator_prompt(registry: list[SkillEntry]) -> str:
    """Build the skill menu section for the orchestrator system prompt.

    Includes only frontmatter info — names, descriptions, dispatch modes.
    The orchestrator reads full skill bodies at runtime via read_file.
    """
    if not registry:
        return ""

    lines = [
        "## Available Skills",
        "",
        "You have the following skills available. To use a skill, first read its",
        'full instructions with read_file("skills/<name>/SKILL.md"), then follow them.',
        "",
    ]

    for skill in registry:
        dispatch = skill.metadata.get("dispatch", "inline")
        tools = skill.metadata.get("tools_allowed", [])
        tools_str = f" | tools: {', '.join(tools)}" if tools else ""
        lines.append(f"- **{skill.name}** ({dispatch}): {skill.description}{tools_str}")

    lines.append("")
    return "\n".join(lines)


def build_skill_files(skills_dir: str = "skills") -> dict[str, str]:
    """Build a dict of path → content for virtual filesystem pre-population.

    All skill files (SKILL.md and references/) are included so the agent
    can read them via the built-in read_file tool.
    """
    files: dict[str, str] = {}
    skills_path = Path(skills_dir)

    if not skills_path.exists():
        return files

    for skill_dir in sorted(skills_path.iterdir()):
        if not skill_dir.is_dir():
            continue

        # Include SKILL.md
        skill_file = skill_dir / "SKILL.md"
        if skill_file.is_file():
            files[str(skill_file)] = skill_file.read_text()

        # Include reference files
        refs_dir = skill_dir / "references"
        if refs_dir.is_dir():
            for ref_file in refs_dir.rglob("*"):
                if ref_file.is_file():
                    files[str(ref_file)] = ref_file.read_text()

    return files


def build_subagents(
    registry: list[SkillEntry],
    default_model_name: str | None = None,
    tool_resolver: Any | None = None,
) -> list[dict[str, Any]]:
    """Build deepagents SubAgent dicts from skills with dispatch: subagent.

    Each subagent gets the full SKILL.md body as its system_prompt.
    Tool filtering uses the tools_allowed list from frontmatter,
    resolved to actual tool objects via tool_resolver.

    SubAgent TypedDict keys (deepagents 0.4.x):
      Required: name, description, system_prompt
      Optional: tools (Sequence[BaseTool]), model, middleware, skills
    """
    subagents: list[dict[str, Any]] = []

    for skill in registry:
        if skill.metadata.get("dispatch") != "subagent":
            continue

        subagent: dict[str, Any] = {
            "name": skill.name,
            "description": skill.description,
            "system_prompt": skill.full_body,
        }

        tools_allowed = skill.metadata.get("tools_allowed")
        if tools_allowed and tool_resolver:
            subagent["tools"] = tool_resolver(tools_allowed)
        # If no resolver, omit tools — subagent inherits all parent tools

        subagents.append(subagent)

    return subagents
