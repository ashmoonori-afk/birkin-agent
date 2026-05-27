---
name: memory-recall
description: Search workspace memory, summaries, run records, and reviews before making continuity-sensitive claims.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["memory", "recall"], "category": "core"}, "openclaw": {"alwaysInclude": true}}
---

# Memory Recall

## When to Use

Use this skill when a task depends on prior decisions, repeated corrections, old run results, or workspace conventions.

## Procedure

1. Search `WORKSPACE_SUMMARY.md`, `memory/`, `runs/`, and `reviews/`.
2. Separate verified current state from older notes.
3. If a remembered fact may be stale, verify it from current files or command output.
4. Update `WORKSPACE_SUMMARY.md` only after the main work and review are complete.

## Pitfalls

- Do not present old notes as current evidence.
- Do not cite memory when the current worktree contradicts it.

## Verification

- The answer or packet identifies the current evidence used.
