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

Birkin is a lightweight Python agent workspace inspired by the direction of
[Hermes Agent](https://github.com/NousResearch/hermes-agent) and
[OpenClaw](https://github.com/openclaw/openclaw).

It is built for people who want the core agent-workspace primitives without installing a
full personal assistant stack: `SKILL.md` skills, scoped subagents, dry-run prompt packets,
self-improvement proposals, and a local operations dashboard.

Birkin is not a fork of Hermes Agent or OpenClaw. It does not vendor their runtime code.
It uses their public repositories as product and architecture references, then keeps the
implementation small and inspectable.

## What It Does

| Area | Birkin behavior |
| --- | --- |
| Skills | Indexes AgentSkills-style `SKILL.md` folders with metadata, precedence, validation, and gating. |
| Hermes coverage | Mirrors all 90 Hermes bundled skill directories and exposes `hermes-<name>` skills with exact upstream source pointers. |
| OpenClaw coverage | Mirrors all 57 OpenClaw upstream skill directories and exposes `openclaw-<name>` skills with exact upstream source pointers. |
| Model selection | Provides Hermes-style model profiles for packet-only runs, Codex CLI, OpenAI-compatible APIs, or any local CLI argv template. |
| Auth | Delegates local CLI OAuth/login state to tools such as `codex` without storing tokens in Birkin. |
| API | Calls OpenAI-compatible chat completions endpoints when an API model profile is selected and executed. |
| Gateway | Serves a local machine-facing HTTP gateway for status, auth, model, API, and run operations. |
| Memory | Writes conversations, feedback, failed runs, and run summaries to an Obsidian-compatible vault and recalls matching notes into chat prompts. |
| Ledger | Maintains `usage/ledger.jsonl` for run status, estimated tokens, provider tokens, and cost fields. |
| Telegram | Provides setup onboarding and test-send support for Telegram bot notifications. |
| Setup | Reports Hermes-style readiness across workspace, models, auth, API, gateway, skills, agents, and chat. |
| Chat | Provides a dashboard chat tab, one-shot `birkin-codex chat`, and Hermes-style `birkin-codex` interactive chat. |
| Subagents | Builds role-scoped prompt packets for planner, builder, reviewer, researcher, and operator agents. |
| Self-improvement | Records lessons, proposes skill patches, and applies approved improvements. |
| CLI | Runs as `birkin-codex` after install, `python -m birkin_agent`, `scripts/birkin-codex`, or `scripts/birkin-codex.ps1`. `birkin` remains a compatibility alias. |
| Dashboard | Shows jobs, result summaries, status, estimated usage, warnings, skills, and agents at `http://127.0.0.1:8765`. |

## Why This Exists

Hermes Agent is a broad self-improving assistant with model routing, messaging gateways,
terminal backends, memory, scheduled automation, subagents, and a full learning loop.
OpenClaw is a local-first personal assistant with many channel, app, node, canvas, and
tool skills.

Birkin takes the parts that are useful for a small agent workspace:

- Skills as procedural memory.
- Subagent prompt packets.
- Run records that can be reviewed.
- Proposal-mode learning instead of silent mutation.
- A dashboard for current jobs and warnings.
- A Python-only core that can run on macOS, Linux, or Windows.

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

Start the dashboard when you want the SaaS-style job and chat UI:

```sh
birkin-codex web --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

## Install as a CLI

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
birkin-codex
birkin-codex doctor
birkin-codex skills validate
birkin-codex web --port 8765
```

On Windows, use `.venv\Scripts\activate` and then the same `pip install -e .` flow.

## Core Commands

```sh
birkin-codex
birkin-codex doctor
birkin-codex setup
birkin-codex setup wizard
birkin-codex skills list
birkin-codex skills validate
birkin-codex skills config
birkin-codex skills create release-checklist --description "Review release readiness."
birkin-codex model list
birkin-codex model use codex-local
birkin-codex auth list
birkin-codex api list
birkin-codex memory status
birkin-codex ledger summary
birkin-codex telegram status
birkin-codex gateway routes
birkin-codex agents list
birkin-codex agents packet planner --model packet --task "Plan the work"
birkin-codex agents run builder --model codex-local --task "Prepare the implementation"
birkin-codex chat --message "Summarize this workspace" --model packet
birkin-codex improve record --lesson "LESSON: Validate skills before running an agent." --skill skill-authoring
birkin-codex improve propose
birkin-codex web --port 8765
```

## Dashboard

The Web UI is a SaaS-style operator dashboard. It is meant for repeated work, not a
marketing page.

It shows:

- Running jobs.
- Recent job results.
- Result summaries.
- Status counts.
- Estimated prompt usage.
- Selectable model profiles.
- Auth, API, and gateway status.
- Obsidian memory, Telegram onboarding, and usage ledger status.
- Setup readiness and skill config status.
- Chat messages through the selected agent and model.
- Enabled and gated skills.
- Agents and their skill allowlists.
- Warnings in a separate panel.

## Skill System

Skills live under:

- `skills/<group>/<skill>/SKILL.md`
- `.agents/skills/<skill>/SKILL.md`
- `managed-skills/<skill>/SKILL.md`
- `bundled-skills/<skill>/SKILL.md`

Earlier roots win when names conflict. A skill may include `references/`, `templates/`,
`scripts/`, and `assets/`, but Birkin indexes only `SKILL.md` by default.

Birkin ships with:

- Core skills for skill authoring, memory recall, subagents, and self-improvement.
- Tool skills for filesystem, shell, web research, browser automation, scheduling, and messaging gateways.
- Development skills for code review, GitHub, documentation, data analysis, and security audit.
- Creative and integration skills.
- 90 Hermes bundled skill reflections under `skills/hermes-reflections/`, backed by exact mirrored source under `skills/upstream/hermes/`.
- 57 OpenClaw reflection skills under `skills/openclaw-reflections/`, backed by exact mirrored source under `skills/upstream/openclaw/`.

See [Hermes Skill Reflection Map](docs/hermes-skill-map.md) and
[OpenClaw Skill Reflection Map](docs/openclaw-skill-map.md).

## Model and Runner Selection

The default model profile is `packet`. It writes a run record and prompt packet without
calling a model. This mirrors the Hermes split between terminal model setup and per-run
model switching, but keeps the implementation local and inspectable. Birkin supports
packet-only, local CLI, and OpenAI-compatible API runners.

List and choose model profiles:

```sh
birkin-codex model list
birkin-codex model use packet
birkin-codex model use codex-local
birkin-codex model use api-openai
```

Run with an explicit model profile:

```sh
birkin-codex agents run builder --model codex-local --execute --task "Implement the change"
```

Configure local CLI profiles in `birkin.json`:

```json
{
  "models": {
    "default": "packet",
    "profiles": {
      "codex-local": {
        "provider": "openai-codex-cli",
        "model": "gpt-5.5",
        "runner": "local-cli",
        "command": ["codex", "exec", "--model", "{model}", "-"],
        "timeoutSeconds": 1800
      }
    }
  }
}
```

You can also add a profile from the local CLI:

```sh
birkin-codex model add codex-fast \
  --provider openai-codex-cli \
  --model gpt-5.5 \
  --runner local-cli \
  --command-json '["codex","exec","--model","{model}","-"]'
```

Keep commands as argv arrays. Do not put shell pipelines or secrets in `birkin.json`.

## Auth, API, and Gateway

Birkin adds Hermes-style integration without storing provider secrets in the workspace.
Local CLI auth profiles delegate login state to the installed tool:

```sh
birkin-codex auth list
birkin-codex auth status codex-cli
birkin-codex auth login codex-cli
```

API profiles target OpenAI-compatible chat completions endpoints:

```sh
birkin-codex api list
birkin-codex agents run builder --model api-openai --execute --task "Draft the change"
```

The gateway is separate from the dashboard UI and exposes local HTTP routes for status,
models, auth, API profiles, and run creation:

```sh
birkin-codex gateway routes
birkin-codex gateway run --port 8770
```

See [Auth, API, and Gateway](docs/auth-api-gateway.md).

## Memory, Ledger, and Telegram

Birkin uses an Obsidian-compatible markdown vault for durable memory. By default it
writes inside `memory/obsidian-vault`, which can be opened as an Obsidian vault or
changed with:

```sh
birkin-codex memory set-vault /path/to/vault --allow-external
birkin-codex memory record --kind feedback --text "USER_CORRECTION: prefer short Korean status updates."
birkin-codex memory recall "Korean status updates"
```

Each run appends a ledger entry:

```sh
birkin-codex ledger summary
birkin-codex ledger list
```

Telegram onboarding records the bot token environment variable and chat id without
storing the token:

```sh
birkin-codex telegram setup --chat-id 123456 --token-env TELEGRAM_BOT_TOKEN --enable
birkin-codex telegram test --message "Birkin is connected."
```

The first-run wizard can configure model, memory, and Telegram in one pass:

```sh
birkin-codex setup wizard
```

## Setup, Chat, and Skill Config

Hermes-style readiness checks:

```sh
birkin-codex setup
birkin-codex setup --json
```

Skill configuration verification:

```sh
birkin-codex skills config
birkin-codex skills validate
```

Dashboard and CLI chat:

```sh
birkin-codex web --port 8765
birkin-codex chat --message "Summarize this workspace" --model packet
```

See [Setup, Chat, and Skill Config](docs/setup-chat-skills.md).

## Advantages

- Lightweight: Python standard library core, no service stack required.
- Inspectable: run records, skill files, and proposals are plain text or JSON.
- Safer by default: dry-run runner, explicit `--execute`, and proposal-mode improvement.
- Portable: macOS/Linux shell script, Windows PowerShell script, and editable Python install.
- Model-profile based: switch between packet-only, Codex CLI, OpenAI-compatible API, or a custom local CLI without code changes.
- Auth-aware: local CLI OAuth is delegated to the tool's own login store instead of saved in Birkin config.
- Gateway-ready: a local HTTP surface can drive runs and status checks from other tools.
- Setup-visible: readiness checks expose incomplete auth, API, gateway, skills, agent, or chat configuration.
- Chat-ready: dashboard and CLI chat reuse the same auditable run records as other agent jobs.
- Memory-backed: chat and run records can be written to an Obsidian vault and recalled into later chat prompts.
- Ledger-backed: every run records estimated usage and provider usage fields in `usage/ledger.jsonl`.
- Hermes-aware: all bundled Hermes skill directories are mirrored and represented as Birkin skills.
- OpenClaw-aware: every upstream OpenClaw skill directory is mirrored and represented as a Birkin skill.
- Dashboard-first operations: job status, result summaries, usage, and warnings are visible immediately.

## Tradeoffs

- Not a drop-in Hermes replacement: no Honcho user model, cloud terminal backend, or scheduler worker yet.
- Not a drop-in OpenClaw replacement: mirrored upstream skills still depend on the local tools and credentials they describe.
- No model calls by default: you must choose a local CLI or API model profile and execute explicitly before real model execution.
- Gateway auth is intentionally small: use the local token gate or bind to localhost for operator workflows.
- Ledger cost is zero until provider-specific pricing is configured; provider token fields are captured when the API returns them.
- macOS script is included, but this repository was initially verified from Windows; macOS should be tested on a real Mac before release claims beyond CLI portability.

## Reference Points

Birkin was shaped by these upstream ideas:

- Hermes README themes: self-improvement, skills, subagents, scheduled automation, model choice, and remote-friendly operation.
- Hermes model docs: terminal model setup plus per-run model override, adapted here as local CLI and API profiles.
- Hermes auth, proxy, and gateway commands: adapted here as local CLI auth profiles, OpenAI-compatible API execution, and a local HTTP gateway.
- Hermes skills docs: `SKILL.md` as procedural memory with progressive disclosure.
- Hermes `skills/`: 90 bundled skill directories mirrored under `skills/upstream/hermes/`.
- OpenClaw README themes: local-first workspace, multi-agent routing, security defaults, channels, canvas, and skills.
- OpenClaw `skills/`: 57 upstream skill directories mirrored under `skills/upstream/openclaw/`.

Local reference notes are in [docs/reference-notes.md](docs/reference-notes.md).

## Verification

```sh
python -m unittest discover -s tests
python -m compileall -q src tests
python -m pip install -e .
birkin-codex doctor
birkin-codex setup
birkin-codex skills validate
birkin-codex skills config
birkin-codex memory status
birkin-codex ledger summary
birkin-codex telegram status
```

Current snapshot:

- Unit tests: 18 passed.
- Upstream skill mirror check: 147 mirrored upstream skills, 0 missing directories.
- Memory smoke check: packet chat wrote Obsidian-compatible notes and recall found them.
- Ledger smoke check: packet chat appended a ledger row with estimated tokens.
- Dashboard smoke check: dashboard status API reported setup status, 9 skill config rows, and chat/setup/memory/ledger/telegram tabs in the served HTML.
- Chat smoke check: `POST /api/chat` returned packet-only status with a reply and run record.
- Gateway smoke check: `GET /health` returned `ok` and `GET /api/setup` returned setup status.
- Code review note: [reviews/2026-05-27-setup-chat-skills-review.md](reviews/2026-05-27-setup-chat-skills-review.md).

## More

- [Architecture](docs/architecture.md)
- [Dashboard](docs/dashboard.md)
- [macOS usage](docs/macos.md)
- [Model selection](docs/model-selection.md)
- [Auth, API, and Gateway](docs/auth-api-gateway.md)
- [Memory, Ledger, and Telegram](docs/memory-ledger-telegram.md)
- [Setup, Chat, and Skill Config](docs/setup-chat-skills.md)
- [Hermes skill map](docs/hermes-skill-map.md)
- [OpenClaw skill map](docs/openclaw-skill-map.md)
- [Reference notes](docs/reference-notes.md)
