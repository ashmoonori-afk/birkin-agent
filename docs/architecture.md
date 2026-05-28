# Architecture

Scope date: 2026-05-28.

Birkin is a lightweight Python implementation of a Hermes-style agent workspace. It uses
Hermes Agent as the reference model for `SKILL.md` driven progressive disclosure and
agent-managed skill evolution, and OpenClaw as the reference model for skill precedence,
gating, operator safety, and broad bundled skill coverage.

Birkin is not a fork of either project. It does not vendor their code or claim runtime
compatibility with their private internals.

## Core Pieces

- `src/birkin_agent/skills.py`: indexes AgentSkills-compatible `SKILL.md` folders,
  frontmatter, precedence, enablement, and OpenClaw-style gates.
- `src/birkin_agent/agents.py`: builds subagent prompt packets with per-agent skill
  allowlists and writes auditable run records.
- `src/birkin_agent/models.py`: resolves Hermes-style model profiles, local CLI
  command templates, defaults, validation, and per-run overrides.
- `src/birkin_agent/auth.py`: manages local CLI OAuth/auth profiles by delegating
  login, logout, and status commands to external CLIs such as `codex`.
- `src/birkin_agent/api.py`: calls OpenAI-compatible chat completions endpoints
  through configured API profiles.
- `src/birkin_agent/runtime.py`: runs the OpenAI-compatible tool-calling agent loop
  used by the `api-agent` model profile.
- `src/birkin_agent/approvals.py`: queues consequential shell, external web,
  Telegram, schedule, and file-write actions for explicit user approval.
- `src/birkin_agent/chat.py`: builds chat-mode tasks and writes normal run records
  through the selected agent and model profile.
- `src/birkin_agent/setup.py`: produces Hermes-style setup checks across workspace,
  models, auth, API, gateway, approvals, Morpheus, skills, agents, and chat.
- `src/birkin_agent/memory.py`: writes and recalls Obsidian-compatible markdown memory
  for conversations, feedback, errors, and run summaries, including semantic
  frontmatter and Obsidian wikilinks.
- `src/birkin_agent/ledger.py`: appends one JSONL ledger entry per run and aggregates
  estimated/provider usage.
- `src/birkin_agent/telegram.py`: stores Telegram onboarding config and sends bot test
  messages using a token environment variable. Optional inbound polling writes
  received messages as conversation memory.
- `src/birkin_agent/morpheus.py`: exposes Morpheus, the 04:00 self-improvement
  review that can run manually or through the local daemon.
- `src/birkin_agent/scheduler.py`: stores approved local schedules and daemon status.
- `src/birkin_agent/gateway.py`: serves a local machine-facing HTTP gateway for
  health, status, model, auth, API, setup, skill config, chat, and run operations.
- `src/birkin_agent/improve.py`: records lessons, gathers signals, creates pending
  skill improvement proposals, and applies approved patches.
- `src/birkin_agent/dashboard.py`: turns run records, usage, warnings, agents, and
  skills into dashboard API data, including model, auth, API, and gateway status.
- `src/birkin_agent/web.py`: serves a local operator dashboard with running jobs,
  result summaries, status, usage, warnings, skills, agents, and job generation.
- `skills/`: bundled starter skill set covering core, tools, development, creative,
  integrations, and product workflows.
- `skills/hermes-reflections/`: one Birkin skill per Hermes bundled upstream skill
  directory, pointing at exact mirrored files under `skills/upstream/hermes/`.
- `skills/openclaw-reflections/`: one Birkin skill per OpenClaw upstream skill
  directory, pointing at exact mirrored files under `skills/upstream/openclaw/`.

## Skill Precedence

Configured roots are checked in order:

1. `skills`
2. `.agents/skills`
3. `managed-skills`
4. `bundled-skills`

The first skill with a given `name` wins. Later duplicates are reported as shadowed.

## Safety Model

- Default runner is `dry-run`.
- Default model profile is `packet`, which never calls an external model.
- Real CLI or API execution requires an explicit model profile in `birkin.json`
  and `--execute` on the run command.
- The `api-agent` runner can call structured tools. Consequential tools are
  queued in approvals instead of executing directly.
- Local CLI OAuth profiles call the external tool's own login store and do not write
  tokens to Birkin config.
- The gateway binds to localhost by default. If `BIRKIN_GATEWAY_TOKEN` is set, or
  `gateway.requireToken` is true, it requires a bearer token or `x-birkin-token`.
- Chat uses the same `--execute` safety boundary as other agent runs.
- Morpheus dry-run works without API keys and does not execute consequential actions.
- `skills config` verifies root, enabled/disabled, gated, precedence, and reflection
  coverage in addition to `SKILL.md` validation.
- Skills are procedural memory, not executable trust.
- Web UI escapes workspace-provided table values before rendering.
- Runtime artifacts live under ignored workspace directories.

## Verification Gates

```sh
python -m unittest discover -s tests
python -m compileall -q src tests
python -m birkin_agent doctor
python -m birkin_agent skills validate
```
