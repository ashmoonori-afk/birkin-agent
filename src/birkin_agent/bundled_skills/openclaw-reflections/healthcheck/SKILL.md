---
name: openclaw-healthcheck
description: "Audit/harden OpenClaw hosts: SSH, firewall, updates, exposure, backups, disk encryption, gateway security."
version: 0.2.0
platforms: [windows, linux, macos]
metadata: {"birkin":{"alwaysInclude":true,"capabilityLevel":"upstream-skill","upstreamMirror":"skills/upstream/openclaw/healthcheck"},"openclaw":{"category":"openclaw","tags":["openclaw","bundled-skill","upstream-skill"],"upstreamCommit":"d00e764e66555320ac75f048c2767ba5877de0a9","upstreamPath":"skills/healthcheck","upstreamSkill":"healthcheck"},"hermes":{"tags":["openclaw","bundled-skill","upstream-skill"],"category":"openclaw"}}
---

# Openclaw Upstream Skill: healthcheck

## Birkin Integration

The exact upstream skill directory is mirrored at `skills/upstream/openclaw/healthcheck`.

When a run asks to include skill bodies, Birkin loads the mirrored upstream `SKILL.md` from that directory.

## Verification

- Upstream source: `skills/healthcheck`
- Upstream commit: `d00e764e66555320ac75f048c2767ba5877de0a9`
- The mirrored directory contains the exact upstream files fetched by `tools/sync_upstream_skills.py`.
