# Architecture

Scope date: 2026-05-28.

Birkin is a lightweight Python implementation of a Hermes-style agent workspace. It uses
Hermes Agent as the reference model for `SKILL.md` driven progressive disclosure and
agent-managed skill evolution, and OpenClaw as the reference model for skill precedence,
gating, operator safety, and broad bundled skill coverage.

Birkin is now positioned as a lite-first verified-learning agent workspace: first-run
chat works in packet mode, advanced operator controls are available when needed, memory
and skill changes are evidence-gated, consequential actions are approval-first, and
runtime health is visible through the local dashboard.

The lite core is intentionally standard-library-only at runtime. `pyproject.toml`
keeps `project.dependencies` empty, and setup/doctor checks verify that policy.

Birkin is not a fork of either project. It does not vendor their code or claim runtime
compatibility with their private internals.

## Core Pieces

- `src/birkin_agent/skills.py`: indexes AgentSkills-compatible `SKILL.md` folders,
  frontmatter, precedence, enablement, and OpenClaw-style gates.
- `src/birkin_agent/agents.py`: builds subagent prompt packets with per-agent skill
  allowlists, Birkin identity, memory digest, and routed skill context, then writes
  auditable run records.
- `src/birkin_agent/models.py`: resolves Hermes-style model profiles, local CLI
  command templates, defaults, validation, and per-run overrides.
- `src/birkin_agent/auth.py`: manages local CLI OAuth/auth profiles by delegating
  login, logout, and status commands to external CLIs such as `codex`.
- `src/birkin_agent/api.py`: calls OpenAI-compatible chat completions endpoints
  through configured API profiles.
- `src/birkin_agent/runtime.py`: runs the OpenAI-compatible tool-calling agent loop
  used by the `api-agent` model profile.
- `src/birkin_agent/runtime_deps.py`: validates the zero-runtime-dependency policy for
  the lite core.
- `src/birkin_agent/approvals.py`: queues consequential shell, external web,
  Telegram, schedule, file-write, and file-delete actions with risk tier, evidence,
  resources, dry-run preview, and rollback hint.
- `src/birkin_agent/chat.py`: builds chat-mode tasks and writes normal run records
  through the selected agent and model profile.
- `src/birkin_agent/setup.py`: produces Hermes-style setup checks across workspace,
  models, memory, skills, agents, and chat, with an advanced option for auth, API,
  gateway, approvals, Morpheus, Telegram, schedules, and ledger status.
- `src/birkin_agent/presets.py` and `src/birkin_agent/experience.py`: define the lite
  skill allowlist and the `lite`/`full` experience switch.
- `src/birkin_agent/memory.py`: writes and recalls typed, scoped, versioned
  Obsidian-compatible markdown memory with evidence, confidence, TTL, append-only
  history, negative-memory revalidation, and wikilinks.
- `src/birkin_agent/learning.py`: records verified-learning events and proposal-mode
  changes with list, show, approve, reject, and rollback operations.
- `src/birkin_agent/reliability.py`: records trace, delivery, health, budget, and
  silent-failure signals for the dashboard, CLI, and gateway.
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
- `src/birkin_agent/dashboard.py`: turns run records, usage, warnings, approvals,
  learning proposals, reliability traces, health, budget, agents, and skills into
  dashboard API data, filtering optional integration warnings in lite mode.
- `src/birkin_agent/web.py`: serves a local operator dashboard with running jobs,
  result summaries, status, usage, warnings, skills, memory, chat, job generation, and
  advanced sections for approvals, learning, reliability, agents, and integrations.
- `skills/`: bundled starter skill set covering core, tools, development, creative,
  integrations, and product workflows.
- `skills/hermes-reflections/`: one Birkin skill per Hermes bundled upstream skill
  directory, pointing at exact mirrored files under `skills/upstream/hermes/`.
- `skills/openclaw-reflections/`: one Birkin skill per OpenClaw upstream skill
  directory, pointing at exact mirrored files under `skills/upstream/openclaw/`.

## Prompt Packets

Every run builds a prompt packet with named sections:

1. Birkin identity and safety boundary.
2. Workspace prompt files such as `AGENTS.md`, `SOUL.md`, and `TOOLS.md`.
3. Obsidian memory digest from keyword recall.
4. Compact skill catalog with names, descriptions, and locations.
5. The user task.
6. Routed skill bodies when requested, and always for local CLI runners.

Local CLI runners therefore receive Birkin identity, memory, and skills through stdin
instead of a bare task string. Birkin still does not try to control the local CLI's
internal tool loop; it gives the CLI enough context to act as Birkin while preserving the
CLI's own auth store and tools.

Debug commands:

```sh
birkin-codex agents packet chat --task "Explain this repo" --format summary
birkin-codex agents packet chat --task "Explain this repo" --format prompt
birkin-codex chat --dry-run --message "Explain this repo"
```

## Skill Precedence

Configured roots are checked in order:

1. `skills`
2. `.agents/skills`
3. `managed-skills`
4. `bundled-skills`

The first skill with a given `name` wins. Later duplicates are reported as shadowed.

Skill discovery is hot-reload friendly: the cache key includes `SKILL.md` mtimes and the
enabled/disabled selection state, so edited skills are rediscovered without a process
restart. `birkin-codex skills sync` is a non-mutating status command for the repo-managed
Hermes/OpenClaw exact mirrors; mirrored upstream files stay immutable and attribution is
preserved.

## Safety Model

- Default runner is `dry-run`.
- Default model profile is `packet`, which never calls an external model.
- Default experience mode is `lite`, which enables a 15-skill core allowlist and hides
  advanced dashboard tabs. `birkin-codex mode use full` restores all eligible skills and
  the full operator surface.
- The lite runtime dependency policy is checked from `pyproject.toml`; non-empty
  `project.dependencies` is treated as a setup/doctor error.
- Real CLI or API execution requires an explicit model profile in `birkin.json`
  and `--execute` on the run command.
- The `api-agent` runner can call structured tools. Consequential tools are
  queued in approvals instead of executing directly.
- Approval queue entries carry `safe`, `review`, `dangerous`, `external`, or
  `irreversible` risk tiers.
- Memory and skill/self-improvement changes write learning events with evidence links.
  Skill changes from agents and Morpheus use proposal mode.
- Upstream and official mirrored skills are immutable; changes must happen through a
  custom fork or a reviewable proposal.
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
