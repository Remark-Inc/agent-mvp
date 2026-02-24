"""Tool registry — maps tool names to LangChain callables."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.web_search import web_search
from tools.fetch_url import fetch_url

# Central registry of all available tools
_TOOL_REGISTRY: dict[str, BaseTool] = {
    "web_search": web_search,
    "fetch_url": fetch_url,
}


def get_tools() -> list[BaseTool]:
    """Return all registered tools."""
    return list(_TOOL_REGISTRY.values())


def get_tools_by_name(names: list[str]) -> list[BaseTool]:
    """Return a filtered subset of tools by name.

    Used for subagent tool filtering based on skill frontmatter's
    tools_allowed list.
    """
    return [_TOOL_REGISTRY[n] for n in names if n in _TOOL_REGISTRY]
