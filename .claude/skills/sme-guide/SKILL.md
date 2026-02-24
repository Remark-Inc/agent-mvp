---
name: sme-iteration-guide
description: >
  Guide for subject matter experts iterating on agent skills, prompts,
  and test scenarios. Load when the user wants to modify agent behavior,
  create or edit skills, run tests, or compare agent runs. Always load
  when working in skills/ or scenarios/ directories.
---

# SME Iteration Guide

You are helping a subject matter expert iterate on an AI agent's behavior.
The SME understands the domain but does not write Python. Help them modify
skills, run tests, and understand results.

## What the SME can safely change

### Skills (skills/*/SKILL.md)
The Markdown body — instructions, guidelines, guardrails, examples.
The `tools_allowed` list (choosing from available tools below).
The `output_schema`. The version number. Reference files in `references/`.

**Do not change:** the `dispatch` field or the "Last message contract"
section. These are engineering concerns. If the SME thinks a skill should
change from inline to subagent or vice versa, note it and ask engineering.

### Test scenarios (skills/*/tests/*.yaml and scenarios/*.yaml)
Create and edit freely based on domain knowledge.

## What the SME should NOT change
- Anything in `orchestrator/`, `tools/`, `scripts/`
- `pyproject.toml`, `.env`

## Iteration workflow

### Modifying a skill
1. Discuss the desired change. Understand the intent.
2. Open `skills/<name>/SKILL.md`. Make a focused edit — one change at a time.
3. Run a test: `python scripts/run.py scenarios/<scenario>.yaml`
4. Review the trace at `runs/<timestamp>/trace.md`.
   - If you see a "⚡ Context summarization event" step, that's normal —
     the agent's memory was automatically compressed to manage context.
     The agent continued working normally after that point.
5. To compare before/after: `python scripts/compare.py runs/<before> runs/<after>`
6. If satisfied: `git add skills/<name>/SKILL.md && git commit -m "skill(<name>): <description>"`

### Creating a test scenario
```yaml
name: "<descriptive name>"
description: >
  <What this tests and why>
input:
  user_request: >
    <The actual user message>
expectations:
  skills_invoked:
    - <skill-name>
  behavior: >
    <Natural language expected behavior>
  max_cost_usd: 2.00
  max_latency_seconds: 120
```
Save to `scenarios/` or `skills/<name>/tests/`.
Run: `python scripts/run.py <path>.yaml`

## Reading the trace
The trace walks through every step the agent took. Key things to look for:
- **Skill activation steps:** which skill was invoked, whether inline or
  as a subagent, what tools it called, what it returned.
- **Orchestrator reasoning steps:** why the agent chose each skill.
- **Context summarization events:** automatic memory compression —
  normal behavior, not an error. Agent continued correctly after.
- **Expectations check:** table at the end showing pass/fail per criterion.

## Available tools (for use in skills)
- `web_search` — searches the web for a query
- `fetch_url` — reads a web page and returns its content

## Tips for writing good skill instructions
- Be specific about what "good" looks like.
- Include guardrails — tell the skill what NOT to do.
- Define output format explicitly. Downstream skills depend on structure.
- Use `references/` for lengthy context instead of putting it inline.
- Keep the SKILL.md body under 500 lines.
- **Do not remove the "Last message contract" section** in subagent skills.
  It is required for the skill to communicate correctly with the orchestrator.

## Commit message convention
`skill(<skill-name>): <short description>`
Examples:
- `skill(research): tighten source recency to 3 months`
- `skill(draft): add conversational tone guidelines`
- `scenario: add edge case for ambiguous user requests`
