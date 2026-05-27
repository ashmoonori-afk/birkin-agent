---
name: hermes-kanban-orchestrator
description: "Lightweight Birkin reflection of the Hermes kanban-orchestrator bundled skill."
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"birkin": {"alwaysInclude": true}, "hermes": {"category": "devops", "tags": ["hermes", "bundled-skill", "reflected-skill"], "upstreamCommit": "bb4703c761ea6687b6399aa2e61e0a08fabd3ca3", "upstreamPath": "skills/devops/kanban-orchestrator", "upstreamSkill": "kanban-orchestrator"}}
---

# Hermes Reflection: Kanban Orchestrator

## Upstream Reference

- Source: `skills/devops/kanban-orchestrator`
- Upstream skill: `kanban-orchestrator`
- Upstream description: "Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The \"don't do the work yourself\" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role."

## When to Use

Use this skill when a task asks for the Hermes `kanban-orchestrator` capability or when a Birkin agent needs to map work to the same bundled-skill intent.

## Procedure

1. Treat this as a lightweight capability marker, not a vendored Hermes implementation.
2. Check whether a native Birkin skill already covers the same capability.
3. If a local CLI, app, credential, model, or service is required, verify it before acting.
4. Keep credentials, account data, and private workspace paths out of run records and skill files.
5. Record a concrete adapter plan before turning this reflection into an executable skill.

## Verification

- The task maps to the upstream Hermes `kanban-orchestrator` bundled skill.
- Required local tools, accounts, services, and platform assumptions are explicitly available.
- A run record or review note states whether execution was direct, dry-run, or deferred.
