"""Main agent definition using deepagents.

Validated import paths (deepagents 0.4.x, langchain 1.2.x):
  - from deepagents import create_deep_agent
  - from langchain.chat_models import init_chat_model
  - from langchain_core.tools import tool
  - from langgraph.checkpoint.memory import InMemorySaver

Subagents are plain dicts: {"name", "description", "prompt", "tools"}.
Virtual filesystem: state["files"] as dict[str, str].
Default model: Claude Sonnet 4 (overridden via AGENT_MODEL env var).
"""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from orchestrator.skill_loader import (
    build_orchestrator_prompt,
    build_skill_files,
    build_subagents,
    load_skill_registry,
)
from orchestrator.tool_registry import get_tools, get_tools_by_name


BASE_INSTRUCTIONS = """\
You are a multi-step AI agent that completes tasks using skills and tools.

## Planning
- Always create a to-do list before starting work.
- Update status as you complete each item.
- If a task has more than 3 steps, break it down further.

## Using Skills
When a task matches a skill's description, use that skill:
1. Read the full skill file with read_file("skills/<name>/SKILL.md").
2. Follow the skill's instructions exactly.
3. For subagent skills, delegate via the task tool — the subagent handles it.
4. For inline skills, execute the instructions yourself.

## Stop Conditions
- Stop after completing all to-do items.
- Stop if you've made 10 tool calls without progress.
- Always write final output to a file before stopping.
"""


def build_agent(
    *,
    model_name: str | None = None,
    skills_dir: str = "skills",
) -> tuple:
    """Build the full agent with skill loader, tools, and subagents.

    Args:
        model_name: Provider:model string (e.g. "openai:gpt-5.2").
                    Falls back to AGENT_MODEL env var.
        skills_dir: Path to skills directory.

    Returns:
        Tuple of (agent graph, initial_files dict for virtual filesystem).
    """
    model_str = model_name or os.environ.get("AGENT_MODEL", "openai:gpt-5.2")
    model = init_chat_model(model_str)

    # Stage 1: Load skill registry (frontmatter only)
    registry = load_skill_registry(skills_dir)

    # Build system prompt with skill menu
    skill_menu = build_orchestrator_prompt(registry)
    instructions = BASE_INSTRUCTIONS + "\n" + skill_menu

    # Build virtual filesystem with skill files
    initial_files = build_skill_files(skills_dir)

    # Build subagent configs from dispatch:subagent skills
    subagents = build_subagents(registry, tool_resolver=get_tools_by_name)

    # Get all registered tools
    tools = get_tools()

    # create_deep_agent returns a CompiledStateGraph directly
    compiled_agent = create_deep_agent(
        model=model,
        tools=tools,
        subagents=subagents,
        system_prompt=instructions,
        checkpointer=InMemorySaver(),
    )

    return compiled_agent, initial_files
