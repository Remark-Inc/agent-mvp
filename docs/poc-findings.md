# POC Findings

## What Worked

1. **deepagents is on PyPI** — `pip install deepagents` works. Version 0.4.3 installed cleanly with all LangGraph dependencies.

2. **`create_deep_agent` API** — works but param names differ from reference docs. Actual: `system_prompt=` (not `instructions=`), `subagents=` (not `sub_agents=`). Returns a `CompiledStateGraph` directly (no `.compile()` call needed).

3. **`init_chat_model` is provider-agnostic** — `from langchain.chat_models import init_chat_model` works. Accepts `"provider:model"` format. Validated with `openai:gpt-5.2`.

4. **SubAgent is a TypedDict** — required keys: `name`, `description`, `system_prompt`. Optional: `tools` (takes BaseTool objects, not string names), `model`. The reference handbook's plain dict format `{"name", "description", "prompt"}` was wrong on the key name.

5. **Skill loader pattern works** — `python-frontmatter` parses YAML frontmatter cleanly. Progressive disclosure (frontmatter at startup, full body on demand) implemented and tested.

6. **Virtual filesystem via `files` dict** — State includes `files: dict[str, str]` for virtual filesystem pre-population. Skill files can be read via built-in `read_file` tool.

7. **Submodule fencing** — agent-mvp as a git submodule at `projects/agent-mvp/` provides clean boundary. CLAUDE.md scoping works: the submodule has its own CLAUDE.md.

## API Mismatches: Reference Docs vs Actual (deepagents 0.4.3)

| What the docs say | What the API actually uses |
|---|---|
| `instructions=` | `system_prompt=` |
| `sub_agents=` | `subagents=` |
| SubAgent `"prompt"` key | `"system_prompt"` key |
| SubAgent `"tools": ["name"]` (strings) | `"tools": [tool_obj]` (BaseTool objects) |
| `agent.compile(checkpointer=...)` | Returns `CompiledStateGraph` directly |
| `CompiledSubAgent` class | Exists but SubAgent TypedDict is the common path |

**Files that still have wrong param names (root repo, not agent-mvp):**
- `AGENTS.md` line 72
- `.claude/refs/langgraph-deep-agents-reference-handbook.md` (multiple sections)
- `.claude/skills/create-agent/SKILL.md`

## What Needs More Work

1. **Full end-to-end scenario run** — smoke test works (single message, no tools). Full scenario with skill dispatch not yet validated.

2. **Subagent dispatch** — research-analyst skill configured as subagent, but not yet tested with a real model call that triggers delegation.

3. **Streaming event format** — `stream_mode="updates"` provides node-level updates but doesn't expose all internal reasoning. `"debug"` mode may give richer traces.

4. **Cost tracking** — Not available from the streaming API. Would need LangSmith trace data or provider-specific response metadata.

5. **Python 3.14 compatibility** — Pydantic V1 deprecation warnings on Python 3.14. Works but noisy. Python 3.12 recommended for production.

## Recommendations

- Pin Python to 3.12 in production deployments
- Add cost tracking via LangSmith API (post-run, not real-time)
- Consider `stream_mode="debug"` for richer traces when debugging
- Add a `scaffold_skill.py` script for consistent skill creation
- Update root repo reference docs with correct API param names
