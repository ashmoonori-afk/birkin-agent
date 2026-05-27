---
name: code-review
description: Review code for correctness, consistency, security, tests, and progress against plan.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["review", "software-development"], "category": "dev"}, "openclaw": {"alwaysInclude": true}}
---

# Code Review

## When to Use

Use this skill after coding, refactoring, or changing automation.

## Procedure

1. Inspect the diff or changed files.
2. Check correctness, consistency, security, and maintainability.
3. Confirm validation commands cover the changed behavior.
4. Write findings first, ordered by severity.
5. If no issues are found, state remaining risk and test gaps.

## Pitfalls

- Do not summarize before findings.
- Do not use tests as proof unless they cover the changed behavior.

## Verification

- A review note exists under `reviews/` for coding tasks.
