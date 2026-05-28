---
name: smart-home
description: Prepare smart-home automations with device allowlists, reversible actions, and safety checks.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["smart-home", "iot"], "category": "integrations"}, "openclaw": {"requires": {"config": ["integrations.smartHome.enabled"]}}}
---

# Smart Home

## When to Use

Use this skill when an agent controls or plans automations for physical devices.

## Procedure

1. Confirm device identity, location, and desired state.
2. Prefer read-only status before control.
3. Require explicit approval for actions that affect access, heat, water, alarms, or safety.
4. Log the command and result.

## Pitfalls

- Do not operate physical devices from ambiguous natural language.
- Do not expose smart-home control to public channels.

## Verification

- The target device and command are explicit and logged.
