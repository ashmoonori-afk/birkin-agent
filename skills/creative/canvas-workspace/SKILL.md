---
name: canvas-workspace
description: Plan visual or canvas-like workspace outputs with explicit state, controls, and validation.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["canvas", "ui"], "category": "creative"}, "openclaw": {"alwaysInclude": true}}
---

# Canvas Workspace

## When to Use

Use this skill when the agent needs a visual workspace, UI state board, or operator control surface.

## Procedure

1. Define the visible objects and controls.
2. Keep state inspectable through files or API endpoints.
3. Verify layout in a browser.
4. Avoid decorative UI that hides operational data.

## Pitfalls

- Do not build a landing page when the task needs a tool.
- Do not put controls where text can overlap at small widths.

## Verification

- The visual surface renders current workspace state.
