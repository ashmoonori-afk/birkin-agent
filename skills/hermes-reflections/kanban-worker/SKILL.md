---
name: hermes-kanban-worker
description: "Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itself is auto-injected into every worker's system prompt as KANBAN_GUIDANCE (from agent/prompt_builder.py); this skill is what you load when you want deeper detail on specific scenarios."
version: 0.2.0
platforms: [linux, macos, windows]
metadata: {"birkin":{"alwaysInclude":true,"capabilityLevel":"upstream-skill","upstreamMirror":"skills/upstream/hermes/devops/kanban-worker"},"hermes":{"category":"devops","tags":["hermes","bundled-skill","upstream-skill"],"upstreamCommit":"2d5dcfabc312d43f87a4f0f44c45f62cf24a09b2","upstreamPath":"skills/devops/kanban-worker","upstreamSkill":"kanban-worker"}}
---

# Hermes Upstream Skill: kanban-worker

## Birkin Integration

The exact upstream skill directory is mirrored at `skills/upstream/hermes/devops/kanban-worker`.

When a run asks to include skill bodies, Birkin loads the mirrored upstream `SKILL.md` from that directory.

## Verification

- Upstream source: `skills/devops/kanban-worker`
- Upstream commit: `2d5dcfabc312d43f87a4f0f44c45f62cf24a09b2`
- The mirrored directory contains the exact upstream files fetched by `tools/sync_upstream_skills.py`.
