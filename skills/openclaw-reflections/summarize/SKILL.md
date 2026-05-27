---
name: openclaw-summarize
description: Lightweight Birkin reflection of the OpenClaw summarize skill.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"openclaw":{"upstreamSkill":"summarize","alwaysInclude":true,"upstreamCommit":"8d6b5997375890608a1bb46a08c1f5a819443d59"},"hermes":{"tags":["openclaw","reflected-skill"],"category":"openclaw-reflection"}}
---

# OpenClaw Reflection: summarize

## When to Use

Use this skill when a task asks for the OpenClaw `summarize` capability or when a Birkin agent needs to route work to a compatible local CLI, integration, or future adapter.

## Procedure

1. Treat this as a lightweight capability marker, not a vendored OpenClaw implementation.
2. Check whether a native Birkin skill already covers the same capability.
3. If a local CLI, app, token, or account is required, verify it before acting.
4. Keep credentials out of run records and skill files.
5. Record a concrete adapter plan before turning this reflection into an executable skill.

## Verification

- The task maps to the upstream OpenClaw `summarize` capability.
- Any required local tool, account, or service is explicitly available.
- A run record or review note states whether execution was direct, dry-run, or deferred.
