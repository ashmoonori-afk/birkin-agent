---
name: subagent-orchestration
description: Split work across scoped subagents using prompt packets, skill allowlists, and auditable run records.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["subagents", "delegation"], "category": "core"}, "openclaw": {"alwaysInclude": true}}
---

# Subagent Orchestration

## When to Use

Use this skill when a task can be divided into independent workstreams or when an agent role needs a narrow skill set.

## Procedure

1. Pick the smallest existing agent that matches the work.
2. Use per-agent skill allowlists for isolation.
3. Build a prompt packet with `birkin agents packet <agent> --task "..."`.
4. Use `birkin agents run <agent> --task "..."` for dry-run records.
5. Enable a real runner only after `birkin.json` contains a reviewed argv command.
6. Review `runs/<timestamp>_<agent>.json` before integrating work.

## Pitfalls

- Do not delegate the immediate blocking task if the main operator needs the result before moving.
- Do not give a subagent all skills when a narrow allowlist is sufficient.
- Do not use shell strings for runner commands.

## Verification

- A run record exists.
- The packet contains only the expected skill catalog.
