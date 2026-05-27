---
name: github
description: Work with GitHub repositories, issues, pull requests, and source references using explicit evidence.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["github", "git"], "category": "dev"}, "openclaw": {"requires": {"bins": ["git"]}}}
---

# GitHub

## When to Use

Use this skill when a task references GitHub source, issues, pull requests, or release state.

## Procedure

1. Prefer primary repository files or official docs.
2. Record the exact URL or local file path inspected.
3. Keep reference clones or notes inside the workspace if artifacts are needed.
4. Check license before copying code.

## Pitfalls

- Do not infer current behavior from stale memory.
- Do not vendor third-party code without an explicit decision.

## Verification

- The reference note includes source URLs.
