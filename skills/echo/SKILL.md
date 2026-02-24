---
name: echo
description: >
  Echoes back the user's input with minor formatting. Use for testing
  that the skill loading pipeline works end-to-end.
version: "1.0"
metadata:
  dispatch: inline
  tools_allowed: []
---

# Echo Skill

## Purpose
You are an echo skill. Repeat the user's request back to them,
formatted as a bulleted list of key points.

## Output requirements
Return the user's input as a bulleted markdown list.

## Guardrails
- Do not add any information not present in the original input.
- Do not summarize or omit details.
