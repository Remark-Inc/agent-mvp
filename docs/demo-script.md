# Demo Script (5 minutes)

## Setup (before demo)

```bash
cd projects/agent-mvp
pip install -e ".[dev]"
# Ensure .env has OPENAI_API_KEY set
```

## Act 1: The Architecture (1 min)

Show the directory structure:
```bash
ls -la skills/
cat skills/research/SKILL.md | head -20
```

**Talking points:**
- Skills are Markdown files, not Python
- YAML frontmatter = config, Markdown body = instructions
- SMEs edit these, engineers don't need to touch them

## Act 2: Run a Scenario (1.5 min)

```bash
AGENT_MODEL=openai:gpt-4o python scripts/run.py scenarios/simple_research.yaml
```

**Talking points:**
- One command runs the full pipeline
- Model is hot-swappable via env var
- Output saved to timestamped runs/ directory

## Act 3: Read the Trace (1 min)

```bash
cat runs/*/trace.md
```

**Talking points:**
- Every step the agent took is visible
- Skills read, tool calls, reasoning — all captured
- SMEs can understand what happened without reading code

## Act 4: Model Hot-Swap (1 min)

```bash
AGENT_MODEL=openai:gpt-4.1-mini python scripts/run.py scenarios/simple_research.yaml
python scripts/compare.py runs/<first> runs/<second>
```

**Talking points:**
- Same scenario, different provider — one env var change
- Compare script shows structural differences
- Proves provider portability

## Act 5: SME Workflow (30 sec)

```bash
# Show the SME guide
cat .claude/skills/sme-guide/SKILL.md | head -30

# Edit a skill (quick change)
# Open skills/research/SKILL.md, change "2-4 targeted search queries" to "3-5"
# Re-run and compare
```

**Talking points:**
- SMEs get guided by Claude Code skills
- Zero Python knowledge needed
- Edit Markdown, run, compare, commit

## Key Messages

1. **Skills as Markdown** — domain experts own the behavior
2. **Provider agnostic** — swap models without code changes
3. **Observable** — every agent decision is traced and readable
4. **Progressive disclosure** — lightweight at startup, detailed on demand
