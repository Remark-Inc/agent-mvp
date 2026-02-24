"""Tests for tools and tool registry."""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from tools.web_search import web_search
from tools.fetch_url import fetch_url
from orchestrator.tool_registry import get_tools, get_tools_by_name


def test_web_search_mock() -> None:
    """web_search returns mock results when no TAVILY_API_KEY."""
    result = web_search.invoke({"query": "python async patterns"})
    assert "python async patterns" in result
    assert "Mock search results" in result or "Result 1" in result


def test_web_search_tool_name() -> None:
    assert web_search.name == "web_search"


def test_fetch_url_tool_name() -> None:
    assert fetch_url.name == "fetch_url"


def test_fetch_url_bad_url() -> None:
    result = fetch_url.invoke({"url": "http://localhost:99999/nonexistent"})
    assert "Error" in result


def test_get_tools_returns_all() -> None:
    tools = get_tools()
    names = [t.name for t in tools]
    assert "web_search" in names
    assert "fetch_url" in names
    assert len(tools) == 2


def test_get_tools_by_name_filter() -> None:
    tools = get_tools_by_name(["web_search"])
    assert len(tools) == 1
    assert tools[0].name == "web_search"


def test_get_tools_by_name_nonexistent() -> None:
    tools = get_tools_by_name(["nonexistent_tool"])
    assert tools == []


def test_get_tools_by_name_empty() -> None:
    tools = get_tools_by_name([])
    assert tools == []
