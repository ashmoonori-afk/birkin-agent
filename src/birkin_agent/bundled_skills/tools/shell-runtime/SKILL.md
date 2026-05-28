---
name: shell-runtime
description: Run local commands safely inside the workspace and report exact failures.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["shell", "runtime"], "category": "tools"}, "openclaw": {"alwaysInclude": true}}
---

# Shell Runtime

## When to Use

Use this skill when command execution is needed for inspection, tests, build, or automation.

## Procedure

1. Set the working directory to the workspace root or a known child directory.
2. Prefer read-only commands before edits.
3. Use exact commands for validation and capture failure text.
4. Keep generated logs under `runs/`, `reviews/`, or another workspace directory.

## Pitfalls

- Do not run destructive recursive operations without a resolved workspace-contained target.
- Do not hide command failures behind retries.

## Verification

- The command output supports the next action.
