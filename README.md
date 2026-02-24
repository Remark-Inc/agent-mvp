# agent-mvp

A skills-based multi-step AI agent where subject matter experts (SMEs) iterate on SKILL.md files via Claude Code, with zero Python knowledge required.

## Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env
# Edit .env — add at least one provider API key

# 3. Run a scenario
python scripts/run.py scenarios/simple_research.yaml

# 4. View the trace
cat runs/*/trace.md

# 5. Compare two runs
python scripts/compare.py runs/<first> runs/<second>
```

## For SMEs

You work in `skills/` and `scenarios/`. No Python needed.

1. **Edit a skill:** Open `skills/<name>/SKILL.md`, modify the instructions
2. **Run a test:** `python scripts/run.py scenarios/<scenario>.yaml`
3. **Read the trace:** `cat runs/<latest>/trace.md`
4. **Compare runs:** `python scripts/compare.py runs/<before> runs/<after>`
5. **Commit:** `git add skills/ && git commit -m "skill(<name>): <description>"`

See `.claude/skills/sme-guide/SKILL.md` for the full iteration guide.

## Project Structure

```
skills/              # SME-owned — SKILL.md files (Markdown + YAML)
scenarios/           # Test scenarios (YAML)
orchestrator/        # Agent assembly (engineering-owned)
tools/               # LangChain tool definitions (engineering-owned)
scripts/             # CLI scripts (engineering-owned)
runs/                # Auto-generated output (gitignored)
.claude/skills/      # Claude Code skills for development workflow
```

## Model Selection

Set `AGENT_MODEL` in `.env` to hot-swap providers:

```bash
AGENT_MODEL=openai:gpt-4o              # OpenAI
AGENT_MODEL=anthropic:claude-sonnet-4-6  # Anthropic
AGENT_MODEL=google_genai:gemini-2.0-flash  # Google
```

Override per-run: `python scripts/run.py scenario.yaml --model openai:gpt-4o`

## Available Skills

| Skill | Type | Description |
|-------|------|-------------|
| research-analyst | subagent | Web research and synthesis |
| draft-writer | inline | Structured text composition |
| analyze | inline | Pattern analysis and insights |
| echo | inline | Test skill (echoes input) |

## Available Tools

| Tool | Description |
|------|-------------|
| web_search | Web search via Tavily (or mock) |
| fetch_url | Fetch and extract text from URLs |
