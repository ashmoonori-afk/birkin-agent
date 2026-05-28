```text
██████╗ ██╗██████╗ ██╗  ██╗██╗███╗   ██╗
██╔══██╗██║██╔══██╗██║ ██╔╝██║████╗  ██║
██████╔╝██║██████╔╝█████╔╝ ██║██╔██╗ ██║
██╔══██╗██║██╔══██╗██╔═██╗ ██║██║╚██╗██║
██████╔╝██║██║  ██║██║  ██╗██║██║ ╚████║
╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
```

**The AI agent that actually remembers you.**

# Birkin Agent

Birkin is a verified-learning, reliability-first agent OS inspired by the direction of
[Hermes Agent](https://github.com/NousResearch/hermes-agent) and
[OpenClaw](https://github.com/openclaw/openclaw).

It is built around one product rule: Birkin should not learn wrong things, should not
silently fail, and should act through approval-first governance.

Birkin is not a fork of Hermes Agent or OpenClaw. It uses their public repositories as
product and architecture references while keeping the Python implementation small,
inspectable, and portable across Windows, macOS, and Linux.

## What It Does

| Area | Birkin behavior |
| --- | --- |
| CLI | Runs as `birkin-codex`; no arguments open the Hermes-style interactive chat CLI. |
| Dashboard | Serves a SaaS-style control plane at `http://127.0.0.1:8765`. |
| Skills | Indexes `SKILL.md` folders with precedence, gating, registry checks, safety metadata, and immutable upstream mirrors. |
| Hermes/OpenClaw mirrors | Mirrors 90 Hermes skill directories and 57 OpenClaw skill directories, with 147 mirrored upstream skills and 0 missing directories. |
| Model selection | Supports packet-only, local CLI, OpenAI-compatible API, and tool-agent profiles without code changes. |
| Auth/API/Gateway | Delegates local CLI OAuth to external tools, supports API-key profiles, and exposes a localhost/token-gated gateway. |
| Memory OS | Stores typed, scoped, versioned Obsidian markdown notes with evidence, confidence, TTL, and append-only history. |
| Verified Learning | Records evidence-backed learning events and proposal-mode changes with approve/reject/rollback commands. |
| Approvals | Risk-tiers shell, external web, Telegram, scheduling, file writes/deletes, and other consequential actions. |
| Reliability | Logs trace events, delivery results, health checks, silent-failure warnings, and token budget status. |
| Telegram | Supports onboarding, explicit test sends, and optional inbound polling without storing bot tokens. |
| Morpheus | Runs conservative self-improvement review; weak evidence becomes proposals instead of silent mutation. |

## Quick Start

### macOS and Linux

```sh
git clone https://github.com/ashmoonori-afk/birkin-agent.git
cd birkin-agent
./scripts/setup
source .venv/bin/activate
birkin-codex setup
birkin-codex
```

### Windows PowerShell

```powershell
git clone https://github.com/ashmoonori-afk/birkin-agent.git
cd birkin-agent
.\scripts\setup.ps1
. .\.venv\Scripts\Activate.ps1
birkin-codex setup
birkin-codex
```

Start the dashboard:

```sh
birkin-codex web --port 8765
```

## Core Commands

```sh
birkin-codex
birkin-codex doctor
birkin-codex setup
birkin-codex setup wizard
birkin-codex model list
birkin-codex model use codex-local
birkin-codex auth list
birkin-codex api list
birkin-codex gateway status
birkin-codex gateway run --port 8770
birkin-codex memory search "model preference" --type preference --scope project
birkin-codex learning list
birkin-codex learning events
birkin-codex learning approve <proposal-id>
birkin-codex learning rollback <event-id>
birkin-codex approvals list
birkin-codex reliability health
birkin-codex reliability traces
birkin-codex reliability budget
birkin-codex skills validate
birkin-codex skills config
birkin-codex skills safety
birkin-codex morpheus --dry-run
birkin-codex chat --message "Summarize this workspace" --model packet
```

## Implemented

- `birkin-codex` Python/pip CLI with Windows PowerShell and macOS/Linux shell scripts.
- Dashboard with jobs, summaries, status, usage, warnings, approvals, learning proposals,
  reliability traces, health, budget, memory, ledger, gateway, Telegram, Morpheus, skills,
  models, API profiles, auth profiles, agents, and chat.
- Obsidian-backed Memory OS for User, Project, Environment, Workflow, Ephemeral,
  Negative, Conversation, Run, Error, and Feedback memories.
- Scope isolation fields for user, project, machine, channel, thread, and profile.
- Versioning, optimistic lock support, TTL expiry metadata, negative-memory revalidation,
  wikilinks, search filters, and append-only `memory/history.jsonl`.
- Verified Learning Loop with evidence links, confidence, TTL, scope, author/agent,
  reason, blame, proposal review, approve/reject, and rollback.
- Approval/risk UX for safe, review, dangerous, external, and irreversible actions.
- Skill safety rows with permissions, version, author/source, computed hash, tests,
  last-verified metadata, immutable upstream detection, and registry consistency checks.
- Morpheus self-improvement that applies only high-evidence safe memory updates and
  turns weak evidence or skill changes into learning proposals.

## Roadmap

- Korea and East Asia integrations: KakaoTalk, LINE, Naver Works, Channel Talk, local
  receipt/payment providers, Upstage Solar, HyperCLOVA X, and Kanana routing.
- Safe skill marketplace with signed packages, permission manifests, regression tests,
  author/version trust, and approval-first installs.
- VPS/systemd and serverless supervisors for always-on operation outside the laptop.
- Additional sandbox backends such as Docker, SSH, Modal, Daytona, Singularity, and
  Vercel-style isolated workers.
- Native MCP server mode so Birkin can expose memory, skills, runs, and approvals to
  other agents.

## Advantages

- Evidence-first learning: memory and skill changes can be traced to conversation, run,
  file, test, approval, or feedback evidence.
- Safer autonomy: consequential actions are queued with risk, resources, dry-run preview,
  rollback hints, and approval history.
- Reliability-first operations: traces, health checks, delivery logs, budget warnings,
  and dashboard warnings make silent failure visible.
- Portable core: the package uses Python and pip, with no service stack required for the
  local CLI and dashboard.
- Upstream-aware skills: Hermes/OpenClaw mirrors remain exact capability references while
  generated changes happen through custom skills or proposals.

## Tradeoffs

- Birkin is not a drop-in Hermes replacement; it does not include Hermes cloud terminal
  backends, Honcho user modeling, or subscription proxy behavior.
- Mirrored upstream skills are intentionally immutable; modifying their behavior requires
  a proposal or custom fork.
- Cost accounting captures token fields and budget warnings, but provider-specific price
  tables are still a future layer.
- Gateway auth is intentionally small; use localhost binding or the token gate for local
  operator workflows.
- Always-on production deployment still needs the roadmap supervisor work.

## Verification

Run:

```sh
python -m pip install -e .
python -m unittest discover -s tests
python -m compileall -q src tests tools
birkin-codex doctor
birkin-codex skills validate
birkin-codex skills config
birkin-codex skills safety
birkin-codex morpheus --dry-run
birkin-codex reliability health
birkin-codex gateway status
```

## More

- [Architecture](docs/architecture.md)
- [Dashboard](docs/dashboard.md)
- [Memory, Ledger, and Telegram](docs/memory-ledger-telegram.md)
- [Runtime, Approvals, and Morpheus](docs/runtime-approval-morpheus.md)
- [Verified Learning and Reliability](docs/verified-learning-reliability.md)
- [Model selection](docs/model-selection.md)
- [Auth, API, and Gateway](docs/auth-api-gateway.md)
- [Setup, Chat, and Skill Config](docs/setup-chat-skills.md)
- [Hermes skill map](docs/hermes-skill-map.md)
- [OpenClaw skill map](docs/openclaw-skill-map.md)
- [Reference notes](docs/reference-notes.md)
