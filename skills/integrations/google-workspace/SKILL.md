---
name: google-workspace
description: Plan Gmail, Calendar, Drive, Docs, and Sheets workflows with explicit credential and approval boundaries.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["google", "workspace"], "category": "integrations"}, "openclaw": {"requires": {"env": ["GOOGLE_APPLICATION_CREDENTIALS"]}}}
---

# Google Workspace

## When to Use

Use this skill when an agent needs to prepare or operate Google Workspace tasks.

## Procedure

1. Confirm the exact account and scope.
2. Use read-only discovery before write actions.
3. Require explicit approval before sending email, changing calendar events, or sharing files.
4. Record only non-sensitive metadata in run records.

## Pitfalls

- Do not store tokens in skill files.
- Do not send messages or share documents from inferred intent.

## Verification

- The requested action, account, and destination are explicit.
