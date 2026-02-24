"""Web search tool — uses Tavily if available, else returns mock results."""

from __future__ import annotations

import os

from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for information on a topic.

    Provide a specific, focused search query. Returns a list of results
    with title, URL, and snippet for each.
    """
    tavily_key = os.environ.get("TAVILY_API_KEY")

    if tavily_key and tavily_key != "...":
        return _tavily_search(query, tavily_key)
    return _mock_search(query)


def _tavily_search(query: str, api_key: str) -> str:
    """Real search via Tavily API."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)
    response = client.search(query, max_results=5)

    results = []
    for r in response.get("results", []):
        results.append(f"- **{r['title']}**\n  {r['url']}\n  {r.get('content', '')[:200]}")

    return "\n\n".join(results) if results else "No results found."


def _mock_search(query: str) -> str:
    """Mock search results for development without API key."""
    return (
        f"[Mock search results for: {query}]\n\n"
        f"- **Result 1**: Example article about {query}\n"
        f"  https://example.com/1\n"
        f"  This is a mock snippet about {query}.\n\n"
        f"- **Result 2**: Another source on {query}\n"
        f"  https://example.com/2\n"
        f"  Additional mock information about {query}."
    )
