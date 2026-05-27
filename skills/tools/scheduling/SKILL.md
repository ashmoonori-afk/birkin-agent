---
name: scheduling
description: Define recurring or background agent work with explicit entrypoints and reviewable outputs.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["cron", "automation"], "category": "tools"}, "openclaw": {"alwaysInclude": true}}
---

# Scheduling

## When to Use

Use this skill when work should run later, repeatedly, or without a live chat turn.

## Procedure

1. Define a workspace-local command entrypoint.
2. Write output to `runs/` or `reports/`.
3. Include owner, cadence, and failure behavior.
4. Run the command manually before scheduling it.

## Pitfalls

- Do not swap a live runner in place when a separate entrypoint is safer.
- Do not schedule work without a visible status artifact.

## Verification

- A manual run record exists before recurring scheduling.
