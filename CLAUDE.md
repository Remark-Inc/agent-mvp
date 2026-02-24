---
name: agent-mvp-dev-guide
description: >
  Guide for developing and maintaining the agent-mvp repository.
  Use when working on orchestrator code, tools, scripts, or infrastructure.
---

# Agent MVP — Developer Guide

## Project overview
A skills-based multi-step AI agent. Skills are SKILL.md files following
the open Agent Skills standard. The orchestrator loads skill frontmatter
at startup (progressive disclosure), reads full skill bodies at runtime,
and dispatches context-heavy skills as subagents.

**Critical design constraint:** SMEs iterate on skills via Claude Code
without touching Python. Everything in the repo is structured for that.

## Directory ownership
- `skills/` — SME-owned. Markdown + YAML only. No Python.
- `scenarios/` — Shared. SMEs create, engineers review.
- `orchestrator/` — Engineering-owned. PR review required.
- `tools/` — Engineering-owned. PR review required.
- `scripts/` — Engineering-owned. PR review required.
- `runs/` — Auto-generated. Gitignored. Never commit.
- `.claude/skills/sme-guide/` — SME-facing skill. Engineering-maintained.
- `.claude/skills/langsmith-fetch/` — Engineer-facing skill. See Development loop.

## Coding conventions

### Python
- Python 3.12+. Type hints on all signatures.
- `click` for CLI scripts. `rich` for console output.
- `python-frontmatter` for SKILL.md parsing.
- `deepagents` as the agent harness. No `claude-agent-sdk`.
- `langchain-core` for tool definitions (`@tool` decorator).
- `langchain.chat_models.init_chat_model` for all model calls.
- No provider SDK (`anthropic`, `openai`) imported in `orchestrator/` or `tools/`.
- No classes unless genuinely needed. Prefer functions and dataclasses.
- Tests use `pytest`.

### Model and provider
- NEVER hardcode a model name. Always read from `os.environ["AGENT_MODEL"]`
  or `skill.metadata.get("model")`.
- NEVER import provider SDKs in orchestrator/ or tools/.

### SKILL.md files
- YAML frontmatter: required fields `name`, `description`, `version`.
- Custom metadata: `dispatch` ("inline" or "subagent"), `model` (optional
  override), `tools_allowed` (list), `max_iterations`, `timeout_seconds`,
  `output_schema`.
- Markdown body: required sections — Purpose, Output requirements,
  Guardrails. If dispatch is subagent, also required: Last message contract
  section explicitly telling the skill to include all output in final message.
- Keep body under 500 lines. Move detail to `references/` subdirectory.
- Use relative links for references: `[rubric](./references/rubric.md)`
- Prefer line-based file formats in references (not heavy markdown tables);
  this enables grep and line-range reads by the agent.

### Scenario YAML
- Required: `name`, `description`, `input`, `expectations`.
- Optional: `model` (pins provider for reproducible comparison).
- Expectations are informational, not hard failures, in the POC.

### Trace output
- `trace.json`: one object per step. `type` field: `orchestrator_reasoning`,
  `skill_read`, `skill_activation`, `tool_call`, `tool_result`,
  `skill_output`, `context_summarization`, `final_output`.
- `trace.md`: human-readable. Use collapsible `<details>` for verbose
  content. **Summarization events must be captured as named steps** with
  a plain-language explanation so SMEs are not confused by history gaps.
- `metadata.json`: scenario, timestamp, model, provider, skill git SHAs,
  cost, latency, whether summarization occurred.

## Progressive disclosure: how skill loading works
1. At startup, `skill_loader.py` reads only YAML frontmatter from each
   `skills/*/SKILL.md` and injects a compact menu into the orchestrator
   system prompt.
2. All skill files are written into the Deep Agents virtual file system
   so the orchestrator can call `read_file("skills/<name>/SKILL.md")`.
3. When the orchestrator decides to use a skill, it reads the full body
   first, then either executes inline or dispatches as a subagent.
4. For `dispatch: subagent` skills, the subagent is pre-configured with
   the full body as its system prompt.

## Last-message contract
Every SKILL.md with `dispatch: subagent` MUST include a prominent section
reminding the skill that only its final message is returned to the
orchestrator. This is enforced in the scaffold template. Review PRs
for this section.

## Development loop (langsmith-fetch)
Engineers should use the `.claude/skills/langsmith-fetch/` skill when
debugging or iterating on agent behavior:
1. Run a scenario: `python scripts/run.py scenarios/<name>.yaml`
2. In a Claude Code session, activate the langsmith-fetch skill
3. Ask Claude Code to fetch recent traces and reflect on what happened
4. Claude Code surfaces prompt or tool improvements
5. Apply changes, re-run, repeat

## Adding a new tool
1. Create `tools/<name>.py` with a `@tool`-decorated function.
2. Register in `tool_registry.py`.
3. Document under "Available tools" below.
4. SMEs can then add the name to any skill's `tools_allowed`.

## Adding a new skill (scaffolding)
`python scripts/scaffold_skill.py <skill-name>`

Creates:
```
skills/<skill-name>/
├── SKILL.md    # template with all required sections including
│               # last-message contract if dispatch: subagent
└── tests/
    └── basic.yaml
```

## Available tools
- `web_search` — searches the web. Input: `query` (str). Returns: list of
  results with title, url, snippet.
- `fetch_url` — fetches and reads a web page. Input: `url` (str). Returns:
  page content as text (truncated to 4000 tokens).

## Running and testing
- Single scenario: `python scripts/run.py scenarios/<name>.yaml`
- With model override: `python scripts/run.py scenarios/<name>.yaml --model openai:gpt-5.2`
- All scenarios: `python scripts/test_scenarios.py`
- All skill tests: `python scripts/test_skills.py`
- Compare two runs: `python scripts/compare.py runs/<a> runs/<b>`
- Scaffold skill: `python scripts/scaffold_skill.py <name>`
