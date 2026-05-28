# Setup, Chat, and Skill Config

Scope date: 2026-05-28.

Birkin includes Hermes-style setup checks, an interactive chat surface, and skill
configuration verification.

## One-Line Install

macOS, Linux, and WSL:

```sh
curl -fsSL https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.sh | sh
birkin-codex
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.ps1 | iex
birkin-codex
```

The installer uses `uv`, `pipx`, or `pip --user`, whichever is available. The
source checkout still supports `scripts/setup` and `scripts/setup.ps1` for editable
local development.

## Setup Check

Run the setup check before using real model execution:

```sh
birkin-codex setup
birkin-codex setup --json
birkin-codex setup check
birkin-codex setup wizard
```

The setup report checks:

- Workspace files and prompt files.
- Model profiles.
- Local CLI auth profiles.
- OpenAI-compatible API profiles.
- Gateway config.
- Obsidian memory.
- Telegram onboarding.
- Usage ledger.
- Skill validation.
- Agent allowlists.
- Chat agent availability.

`OPENAI_API_KEY` is reported as a warning when the default OpenAI-compatible API profile
is configured but the environment variable is not set.

## Chat

The dashboard includes a `Chat` tab. The default `chat` agent uses these skills:

- `memory-recall`
- `taskflow`
- `documentation`

Hermes-style interactive terminal chat:

```sh
birkin-codex
```

Interactive commands:

- `/live` switches to the best available live model profile and turns execution on.
- `/setup` shows readiness checks.
- `/dashboard` shows the local dashboard command and URL.
- `/skills` shows skill configuration checks.
- `/model ID` switches the model profile for the current chat.
- `/execute on` allows the selected runner to execute.
- `/execute off` returns to packet-only safe mode.
- `/exit` leaves chat.

Packet-only chat:

```sh
birkin-codex chat --message "Summarize this workspace" --model packet
```

Packet mode is the first-run success path. It creates a run record, recalls memory,
captures the conversation, and explains how to switch to live execution without
requiring API keys up front.

Executed chat through a configured model profile:

```sh
birkin-codex chat --message "Draft the next plan" --model codex-local --execute
```

The dashboard chat form uses `/api/chat`. The gateway exposes the same operation at
`POST /api/chat`.

## Skill Config Verification

Run:

```sh
birkin-codex skills config
birkin-codex skills config --json
birkin-codex skills validate
birkin-codex skills safety
```

`skills config` reports:

- Configured skill roots.
- Discovered skill count.
- Enabled and eligible skill count.
- Gated skill count.
- Shadowed duplicate skill files.
- Enabled/disabled selection state.
- Hermes and OpenClaw reflection counts.
- Exact upstream mirror completeness.
- Registry consistency for canonical id, path, source, enabled state, and list/view agreement.
- Skill safety summary for permission metadata, versions, hashes, and immutable upstream mirrors.

This check is separate from `skills validate`, which still validates each `SKILL.md`
frontmatter and body. `skills validate` also includes the config-level checks.

`skills safety` lists per-skill permission manifest, version, author/source, computed
hash, tests, last verified value, and whether the skill is immutable.
