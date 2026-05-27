---
name: hermes-minecraft-modpack-server
description: "Lightweight Birkin reflection of the Hermes minecraft-modpack-server bundled skill."
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"birkin": {"alwaysInclude": true}, "hermes": {"category": "gaming", "tags": ["hermes", "bundled-skill", "reflected-skill"], "upstreamCommit": "bb4703c761ea6687b6399aa2e61e0a08fabd3ca3", "upstreamPath": "skills/gaming/minecraft-modpack-server", "upstreamSkill": "minecraft-modpack-server"}}
---

# Hermes Reflection: Minecraft Modpack Server

## Upstream Reference

- Source: `skills/gaming/minecraft-modpack-server`
- Upstream skill: `minecraft-modpack-server`
- Upstream description: "Host modded Minecraft servers (CurseForge, Modrinth)."

## When to Use

Use this skill when a task asks for the Hermes `minecraft-modpack-server` capability or when a Birkin agent needs to map work to the same bundled-skill intent.

## Procedure

1. Treat this as a lightweight capability marker, not a vendored Hermes implementation.
2. Check whether a native Birkin skill already covers the same capability.
3. If a local CLI, app, credential, model, or service is required, verify it before acting.
4. Keep credentials, account data, and private workspace paths out of run records and skill files.
5. Record a concrete adapter plan before turning this reflection into an executable skill.

## Verification

- The task maps to the upstream Hermes `minecraft-modpack-server` bundled skill.
- Required local tools, accounts, services, and platform assumptions are explicitly available.
- A run record or review note states whether execution was direct, dry-run, or deferred.
