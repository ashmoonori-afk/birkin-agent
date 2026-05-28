---
name: filesystem
description: Read, create, and update workspace files with path containment and minimal unrelated churn.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["files", "workspace"], "category": "tools"}, "openclaw": {"alwaysInclude": true}}
---

# Filesystem

## When to Use

Use this skill when the agent needs to inspect or edit files.

## Procedure

1. Resolve paths relative to the workspace.
2. Confirm the target stays inside the workspace.
3. Prefer small patches over broad rewrites.
4. Leave unrelated files untouched.
5. Keep scratch outputs in a named workspace folder.

## Pitfalls

- Do not follow untrusted symlinks out of the workspace.
- Do not delete generated or user files unless the task requires it.

## Verification

- `birkin doctor` and relevant tests still pass.
