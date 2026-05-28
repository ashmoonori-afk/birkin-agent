---
name: taskflow
description: Convert broad requests into ordered tasks, dependencies, status updates, and completion evidence.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["planning", "taskflow"], "category": "product"}, "openclaw": {"alwaysInclude": true}}
---

# Taskflow

## When to Use

Use this skill when work has multiple steps, dependencies, or visible progress requirements.

## Procedure

1. Derive concrete requirements from the user request.
2. Identify evidence needed for each requirement.
3. Keep a short plan with one active step.
4. Update status after meaningful progress.
5. Audit completion against evidence before claiming done.

## Pitfalls

- Do not redefine success around the easiest subset.
- Do not treat a passing narrow check as proof of a broad requirement.

## Verification

- The final status maps to the original request.
