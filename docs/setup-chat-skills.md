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

The default setup report runs in lite mode. It checks:

- Runtime dependency policy.
- Workspace files and prompt files.
- Model profiles.
- Obsidian memory.
- Skill validation.
- Agent allowlists.
- Chat agent availability.

Advanced setup checks are available when the user is ready to connect integrations:

```sh
birkin-codex setup --advanced
birkin-codex doctor --advanced
birkin-codex mode use full
```

Advanced checks add local CLI auth profiles, OpenAI-compatible API profiles, gateway
config, Telegram onboarding, approval queues, Morpheus, schedules, and usage ledger
status. `OPENAI_API_KEY` is reported as a warning only in advanced/full checks when the
default OpenAI-compatible API profile is configured but the environment variable is not
set.

## Experience Mode

Birkin starts in `lite` mode:

```sh
birkin-codex mode status
birkin-codex mode use full
birkin-codex mode use lite
```

`lite` mode keeps a 15-skill core allowlist and hides advanced dashboard tabs by default.
`full` mode enables all eligible discovered skills and shows the full operator surface.

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
- `/mode lite` switches back to the small default surface.
- `/mode full` enables all eligible skills and advanced controls.
- `/model ID` switches the model profile for the current chat.
- `/execute on` allows the selected runner to execute.
- `/execute off` returns to packet-only safe mode.
- `/exit` leaves chat.

Packet-only chat:

```sh
birkin-codex chat --message "Summarize this workspace" --model packet
birkin-codex chat --dry-run --message "Summarize this workspace"
```

Packet mode is the first-run success path. It creates a run record, recalls memory,
captures the conversation, and explains how to switch to live execution without
requiring API keys up front.

Prompt packet debugging:

```sh
birkin-codex agents packet chat --task "Summarize this workspace" --format summary
birkin-codex agents packet chat --task "Summarize this workspace" --format prompt
```

The summary format reports the agent, model, runner, prompt style, sections, routed
skills, recalled memory count, estimated tokens, and prompt size. The prompt format
prints the exact text sent to packet/API/local CLI runners.

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
birkin-codex skills sync
birkin-codex skills sync --json
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

`skills sync` is intentionally non-mutating in this repo. Birkin Codex already ships exact
Hermes/OpenClaw mirrors under `skills/upstream`, and those upstream mirrors are immutable.
The command reports mirror health, the hot-reload policy, and the enabled+eligible gating
policy without copying over existing upstream files.

This check is separate from `skills validate`, which still validates each `SKILL.md`
frontmatter and body. `skills validate` also includes the config-level checks.

`skills safety` lists per-skill permission manifest, version, author/source, computed
hash, tests, last verified value, and whether the skill is immutable.
