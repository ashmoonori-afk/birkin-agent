---
name: browser-automation
description: Verify local Web UI behavior with a browser after frontend changes.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["browser", "ui"], "category": "tools"}, "openclaw": {"alwaysInclude": true}}
---

# Browser Automation

## When to Use

Use this skill after building or changing a Web UI.

## Procedure

1. Start the local server from the workspace.
2. Open the localhost URL.
3. Check visible layout, navigation, API-backed tables, and console errors.
4. Capture the exact URL and any failure details.

## Pitfalls

- Do not claim the Web UI works from server startup alone.
- Do not ignore mobile layout if the UI is operator-facing.

## Verification

- The page loads and shows skills, agents, and a run packet action.
