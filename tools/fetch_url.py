"""URL fetching tool — fetches a web page, strips HTML, truncates."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from io import StringIO
from urllib.request import Request, urlopen
from urllib.error import URLError

from langchain_core.tools import tool

MAX_CHARS = 16000  # ~4000 tokens


class _HTMLTextExtractor(HTMLParser):
    """Simple HTML-to-text converter."""

    def __init__(self) -> None:
        super().__init__()
        self._output = StringIO()
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._output.write(data)

    def get_text(self) -> str:
        return self._output.getvalue()


@tool
def fetch_url(url: str) -> str:
    """Fetch a web page and return its text content.

    Strips HTML tags, scripts, and styles. Truncates to ~4000 tokens.
    Use this to read the full content of a specific URL found via web_search.
    """
    try:
        req = Request(url, headers={"User-Agent": "agent-mvp/0.1"})
        with urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError, OSError) as e:
        return f"Error fetching {url}: {e}"

    # Strip HTML
    extractor = _HTMLTextExtractor()
    extractor.feed(raw)
    text = extractor.get_text()

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[Truncated — content exceeded 4000 token limit]"

    return text if text else "No readable content found at this URL."
