# POC Findings

## What Worked

1. **deepagents is on PyPI** — `pip install deepagents` works. Version 0.4.3 installed cleanly with all LangGraph dependencies.

2. **`create_deep_agent` API matches documentation** — takes `model`, `tools`, `sub_agents`, `instructions` as expected. Returns a LangGraph graph that compiles with `InMemorySaver`.

3. **`init_chat_model` is provider-agnostic** — `from langchain.chat_models import init_chat_model` works. Accepts `"provider:model"` format. Validated for openai, anthropic providers.

4. **Subagents are plain dicts** — `{"name", "description", "prompt", "tools"}` format confirmed. No `CompiledSubAgent` class needed (as suspected in API mismatch #1).

5. **Skill loader pattern works** — `python-frontmatter` parses YAML frontmatter cleanly. Progressive disclosure (frontmatter at startup, full body on demand) implemented and tested.

6. **Virtual filesystem via `files` dict** — State includes `files: dict[str, str]` for virtual filesystem pre-population. Skill files can be read via built-in `read_file` tool.

7. **Submodule fencing** — agent-mvp as a git submodule at `projects/agent-mvp/` provides clean boundary. CLAUDE.md scoping works: the submodule has its own CLAUDE.md.

## API Mismatches Confirmed

1. **`CompiledSubAgent` doesn't exist** — confirmed. Subagents are plain dicts. Design doc reference was incorrect.

2. **Virtual filesystem** — `files: dict[str, str]` in state, pre-populated via initial invoke state. Works as documented.

3. **`init_chat_model` import** — `from langchain.chat_models import init_chat_model` is the correct path for langchain 1.2.x.

4. **Summarization events** — not directly hookable via the stream API in `updates` mode. Tracer captures what's available; summarization detection relies on heuristics.

5. **Default model** — deepagents defaults to Claude Sonnet 4 via `ChatAnthropic`. Overriding with `init_chat_model` works correctly.

## What Needs More Work

1. **Streaming event format** — `stream_mode="updates"` provides node-level updates but doesn't expose all internal reasoning. `"debug"` mode may give more detail but produces significantly more data.

2. **Subagent tool filtering** — Subagent `tools` field accepts string names, but the actual filtering mechanism needs more testing to confirm it works correctly with `get_tools_by_name`.

3. **Cost tracking** — Not available from the streaming API. Would need LangSmith trace data or provider-specific response metadata.

4. **Python 3.14 compatibility** — Pydantic V1 deprecation warnings on Python 3.14. Works but noisy. Python 3.12 recommended for production.

## Recommendations

- Pin Python to 3.12 in production deployments
- Add cost tracking via LangSmith API (post-run, not real-time)
- Consider `stream_mode="debug"` for richer traces when debugging
- Add a `scaffold_skill.py` script for consistent skill creation
