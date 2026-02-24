---
name: langsmith-fetch-debugger
description: >
  Fetches and analyzes agent execution traces from LangSmith to support
  debugging and iterative improvement. Use when an engineer wants to
  understand why the agent behaved a certain way, identify prompt or
  tool improvements, or run the agent development loop.
---

# LangSmith Fetch Debugger

You are helping an engineer debug and improve the agent by analyzing
LangSmith traces. Use the langsmith-fetch CLI to pull trace data and
reflect on what it reveals.

## Prerequisites
- `langsmith-fetch` installed (`pip install langsmith-fetch`)
- `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` set in environment

## The development loop

1. Run the agent: `python scripts/run.py scenarios/<name>.yaml`
2. Fetch the most recent trace: `langsmith-fetch traces --limit 1`
3. Analyze the trace: look for inefficiencies, errors, unexpected paths
4. Suggest targeted improvements to skill instructions, tool schemas,
   or orchestrator prompt
5. Apply the change, re-run, compare

## Useful commands
```bash
langsmith-fetch traces                          # most recent trace
langsmith-fetch traces --limit 5                # last 5 traces
langsmith-fetch traces --last-n-minutes 30      # last 30 minutes
langsmith-fetch threads                          # full conversation threads
```

## What to look for in traces
- **Unnecessary tool calls:** Is the agent calling fetch_url when search
  snippets would suffice? Suggests a prompt tightening opportunity.
- **Skill not invoked when expected:** Is the orchestrator routing to the
  wrong skill? Suggests the skill description in frontmatter needs sharpening.
- **Subagent last message missing data:** Did the subagent fail to include
  findings in its final response? The "Last message contract" section in the
  skill needs strengthening.
- **Context summarization triggering early:** Is summarization firing before
  the agent completes? May indicate a skill is being too verbose in tool calls.
- **High cost steps:** Which tool calls or skill activations dominate cost?
  Are they justified?

## Skill learning workflow
After a successful agent run, use the trace to capture what worked as a
new or updated skill:
1. Fetch the trace: `langsmith-fetch traces --limit 1`
2. Reflect: what procedure did the agent follow? Was it effective?
3. If yes, draft or update a `skills/<name>/SKILL.md` capturing the
   procedure as reusable instructions
4. Validate the skill format (required sections, frontmatter fields)
5. Commit: `git add skills/<name>/ && git commit -m "skill(<name>): learned from trace <id>"`
