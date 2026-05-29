# Workspace Summary

Last updated: 2026-05-28

## Purpose

Birkin Codex is a lite-first Hermes-style Python agent workspace. It provides
`SKILL.md` skill management, scoped subagent prompt packets, local CLI/API model
execution, an OpenAI-compatible tool-calling runtime, approval-gated consequential
actions, semantic Obsidian memory, a usage ledger, Telegram onboarding/inbound polling,
Morpheus self-improvement, a machine-facing gateway, and a local dashboard with advanced
operator controls hidden by default.

## Current State

- Python package: `src/birkin_agent`.
- Primary CLI entrypoint: `birkin-codex` via editable install. With no arguments it opens
  the Hermes-style interactive chat CLI.
- Compatibility CLI alias: `birkin`.
- Default experience: `lite`, with 15 core skills enabled and optional API/Telegram
  warnings hidden from the default `doctor`, setup, and dashboard surface. `birkin-codex
  mode use full` restores all eligible discovered skills and shows the full operator
  surface; `birkin-codex doctor --advanced` shows optional integration warnings.
- Lite runtime policy: `pyproject.toml` keeps `project.dependencies` empty, and
  `src/birkin_agent/runtime_deps.py` makes setup/doctor fail if package runtime
  dependencies are added to the core path.
- One-line installers: `scripts/install.sh` for macOS/Linux/WSL and
  `scripts/install.ps1` for Windows PowerShell. Both install from
  `https://github.com/ashmoonori-afk/birkin-agent` with `uv`, `pipx`, or
  `pip --user`, and honor `BIRKIN_REPO`/`BIRKIN_REF` overrides.
- Self-update command: `birkin-codex update` reinstalls from `BIRKIN_REPO`/`BIRKIN_REF`
  or the default GitHub `main` ref, using `uv`, `pipx`, or `pip`. It supports
  `--dry-run`, `--json`, `--repo`, `--ref`, and `--method auto|uv|pipx|pip`.
- Script entrypoints: `scripts/setup`, `scripts/setup.ps1`, `scripts/birkin-codex`,
  `scripts/birkin-codex.ps1`, `scripts/birkin`, and `scripts/birkin.ps1`.
- Model profiles: `packet`, `codex-local`, `api-openai`, `api-agent`, and
  `custom-local`.
- Runners: packet-only `dry-run`, command-based `local-cli`, plain OpenAI-compatible
  `api`, and OpenAI-compatible `tool-agent`.
- Prompt packets: all packets include Birkin identity, prompt files, Obsidian memory
  digest, compact skill catalog, and task. Local CLI profiles automatically receive
  routed skill bodies too, so Codex/Claude/local commands act with Birkin context instead
  of receiving a bare prompt.
- Packet debugging: `birkin-codex agents packet ... --format summary|prompt` and
  `birkin-codex chat --dry-run` expose the exact prompt path without making model calls.
- Tool-agent runtime: can load skills, write/search/get/link memory, read/list files,
  queue file writes, queue shell/web/Telegram/schedule actions, and spawn scoped
  packet-only subagents. If a tool-agent attempts to replace an existing memory note
  without an expected version or append mode, Birkin queues a verified-learning proposal
  instead of overwriting it. Tool-agent skill creation also becomes a learning proposal
  rather than a direct `SKILL.md` write.
- Approval gate: `birkin-codex approvals list|approve|reject`; pending approvals are
  stored under `approvals/pending` and history under `approvals/history`. Approval rows
  now include risk tier, evidence count, affected resources, dry-run preview, and
  rollback hint.
- Verified Learning Loop: `src/birkin_agent/learning.py` records evidence-backed memory,
  skill, and self-improvement events under `learning/events.jsonl` and reviewable
  proposals under `learning/proposals`. CLI commands include
  `learning list|events|show|approve|reject|rollback`.
- Memory OS: typed, scoped, versioned Obsidian markdown under `memory/obsidian-vault`,
  preserving old folders and adding User, Project, Environment, Workflow, Ephemeral, and
  Negative memory folders. Notes include `kind`, `type`, `version`, `scope`,
  `confidence`, `sources`, `evidence`, `ttlDays`, `expires`, `author`, `agent`,
  `reason`, `blame`, append-only `memory/history.jsonl`, negative-memory revalidation,
  and Obsidian `[[wikilink]]` support.
- Ledger: `usage/ledger.jsonl` for run status, estimated tokens, provider token fields,
  and cost fields.
- Reliability control plane: `src/birkin_agent/reliability.py` writes
  `reliability/events.jsonl`, exposes health checks, trace rows, delivery rows,
  replay records, silent-failure warnings, and per-run/daily/monthly token budget status.
- Telegram: env-only bot token config, explicit test-send, and optional inbound polling.
  Runtime-requested outbound sends go through approvals.
- Morpheus: `birkin-codex morpheus --dry-run` and daemon support for the 04:00
  self-improvement review. Morpheus applies only high-evidence safe memory updates; weak
  evidence and all skill updates become verified-learning proposals.
- Gateway: `birkin-codex gateway run --port 8770`, serving local HTTP status, model,
  auth, API, memory, ledger, learning, reliability, Telegram, approvals, schedules,
  daemon, Morpheus, chat, and run routes. Gateway token behavior remains localhost/token
  based.
- Web UI: `birkin-codex web --port 8765`, showing jobs, summaries, status, usage,
  warnings, memory, skills, setup, and chat first. Models, auth, API, gateway, ledger,
  Telegram, approvals, learning, reliability, Morpheus, schedules, agents, and daemon
  controls remain available behind the `Show Advanced` toggle in lite mode. The learning
  tab can list, show, approve, reject, and rollback learning records through the local
  API. The job panel is now framed as `Try Safe Packet`; runner execution controls are
  advanced-only in lite mode.
- Skill safety: `birkin-codex skills safety` lists permission manifest, version,
  author/source, computed hash, tests, last verified, immutable status, and path.
  `skills config` now includes registry consistency and skill-safety rows.
- Skill sync: `birkin-codex skills sync` is a non-mutating status command for the
  repo-managed Hermes/OpenClaw exact mirrors. It reports mirror health, hot-reload cache
  behavior, and enabled+eligible packet injection policy.
- Setup wizard: model selection, Obsidian vault setup, Telegram onboarding, and optional
  Telegram inbound.
- Chat-first UX: no-argument `birkin-codex` opens the interactive chat with safe packet
  mode explained up front. The startup screen shows the Birkin ASCII banner, memory
  tagline, selected model label, enabled skill count, and Obsidian vault path. Packet-only
  chat now returns a first-run success message that confirms a run record was created and
  explains live execution instead of only reporting that no model runner executed. The
  chat payload still includes `memoryNote` when memory capture succeeds.
- Slash command UX: `/`, `/help`, and `/commands` show a command picker; `/status`
  reports active agent, model, mode, skill count, execution state, and vault. Readline
  shells get slash command Tab completion when available. `/update --dry-run` previews
  the self-update command, and `/update` runs it.
- Live chat handoff: `/live` selects `api-agent` when `OPENAI_API_KEY` is present,
  `codex-local` when the local `codex` CLI is available, or another runnable configured
  profile, then turns execution on for the current chat.
- Bundled skill bootstrap: `src/birkin_agent/bundled_skills` is packaged with pip/uv
  installs. Skill commands, setup, dashboard data, and agent packet building repair
  missing bundled skills before discovery without overwriting existing user files.
  Bundled upstream copies preserve upstream `SKILL.md` bodies, with `.gitattributes`
  limiting whitespace checks for those copied upstream files only.
- Default agents: planner, builder, reviewer, researcher, operator, and chat.
- Upstream skills: 90 Hermes and 57 OpenClaw exact mirrored upstream skill directories,
  with 147 mirrored upstream skills and 0 missing directories.

## Claude Birkin Reference Port

Ported ideas:

- Small tool-calling loop and registry shape.
- Obsidian memory tools and wikilinks.
- Approval queue before consequential actions.
- Unattended self-improvement review, renamed Morpheus.
- Telegram channel concept with env-only token handling.

Kept different:

- Birkin Codex keeps its existing dashboard, ledger, model/auth/API profiles, tests, and
  exact Hermes/OpenClaw upstream mirrors.
- The default runner remains packet-only.
- Local CLI profiles remain command runners; structured tools are available through the
  OpenAI-compatible `tool-agent` profile.
- Morpheus dry-run is deterministic and no-key safe.

## Verification Snapshot

- `py -m pip install -e .`: passed for Python 3.13, but that Scripts directory is not
  on this shell's PATH.
- `py -3.12 -m pip install -e .`: passed and installed `birkin-codex` into a Scripts
  directory already on PATH.
- `birkin-codex mode status`: passed directly from the terminal and reported
  `mode=lite`, `enabledCount=15`.
- `py -m compileall -q src tests tools`: passed.
- `py -m unittest discover -s tests`: 36 tests passed after adding the update command.
- `git diff --check -- . ':!skills/upstream'`: passed.
- `birkin-codex doctor`: `ok` in lite mode.
- `birkin-codex doctor --advanced`: `ok` with expected warnings for missing
  `OPENAI_API_KEY` and Telegram not enabled.
- `birkin-codex setup --json`: passed with lite checks only and runtime dependency
  check `ok`.
- `birkin-codex setup --advanced --json`: passed with expected optional integration
  warnings.
- `birkin-codex mode status`: passed and reported `mode=lite`, `enabledCount=15`.
- `birkin-codex update --dry-run --method pip --json`: passed and reported
  `python -m pip install --upgrade --user git+https://github.com/ashmoonori-afk/birkin-agent@main`.
- Interactive skill smoke with piped chat input passed: `/skills` shows a compact
  enabled-skill catalog, `/skill memory-recall` shows detail and the body command, and
  `/skills health` shows the full catalog health table.
- Full structure and agent review passed the green-path checks but found risk areas:
  non-local Web UI/gateway bind exposure, tool-agent turn-limit runs recorded as `ok`,
  pip wheels shipping only bundled `SKILL.md` files instead of support assets, and
  interactive `/model` accepting missing profiles silently.
- Review findings remediation: Web UI POST execution endpoints are local-client only,
  gateway non-localhost binds require token auth, tool-agent turn-limit exits are recorded
  as failed, pip wheels include the full bundled skill support tree without pycache, and
  interactive `/model` rejects unknown profiles.
- `birkin-codex skills validate`: `ok`.
- `birkin-codex skills config`: passed with 168 discovered skills, 15 enabled, 90 Hermes
  reflections, 57 OpenClaw reflections, and 147 mirrored upstream skills.
- `birkin-codex skills sync --json`: passed and reported repo-managed mirrors, dry-run
  status, 147 mirrored upstream skills, and 0 missing directories.
- `birkin-codex skills config --json`: passed; upstream mirror check reports 147
  mirrored upstream skills and 0 missing directories. Registry consistency and
  skill-safety checks are `ok`.
- `birkin-codex skills safety --json`: passed.
- `birkin-codex agents packet builder --model codex-local --task "Plan a refactor"
  --format summary`: passed with `cli-agent` style and `skillBodies`.
- `birkin-codex agents packet builder --model codex-local --task "Plan a refactor"
  --format prompt`: passed and included `Birkin Identity`, `Memory Digest`, and routed
  `## Skill:` bodies.
- `birkin-codex morpheus --dry-run --json`: passed and wrote a Morpheus run record.
- `birkin-codex learning list --json`: passed.
- `birkin-codex learning events --json`: passed.
- `birkin-codex reliability health --json`: passed with expected warnings for optional
  Morpheus daemon, Telegram, and API key setup.
- `birkin-codex reliability budget --json`: passed.
- `birkin-codex approvals list --json`: passed.
- `birkin-codex gateway status --json`: passed and includes learning/reliability routes.
- Dashboard smoke on `127.0.0.1:8768`: `/api/status` included learning proposals,
  reliability log, traces, replay records, health, and budget fields.
- Dashboard smoke on `127.0.0.1:8771` with headless Edge: title rendered as `Birkin
  Agent`, advanced tabs were hidden in lite mode, visible after `Show Advanced`, and the
  warning metric was `0`.
- Dashboard smoke on `127.0.0.1:8786` with headless Edge: title rendered as `Birkin
  Agent`, `Try Safe Packet` and `Build Packet` rendered, advanced navigation and execute
  controls were hidden in lite mode, and both became visible after `Show Advanced`.
- Empty workspace smoke from `%TEMP%`: `birkin-codex init` then
  `birkin-codex skills config` repaired the skill catalog to 168 discovered skills and
  no config errors.
- Wheel smoke: `py -m pip wheel . --no-deps` produced a wheel containing 315 bundled
  `SKILL.md` files.
- Gateway smoke on `127.0.0.1:8772`: `/health`, `/api/reliability`, and `/api/learning`
  passed, including reliability replay records.
- Code review note: `reviews/2026-05-28-verified-learning-reliability-review.md`.
- Installer/chat UX review note: `reviews/2026-05-28-installer-chat-ux-review.md`.
- Lite mode review note: `reviews/2026-05-28-lite-mode-review.md`.
- Lite CLI packet review note: `reviews/2026-05-28-lite-cli-packet-review.md`.
- Startup/slash/skills review note: `reviews/2026-05-28-startup-slash-skills-review.md`.
- Latest code review note: `reviews/2026-05-28-update-command-review.md`.
- Skills display review note: `reviews/2026-05-28-skills-display-review.md`.
- Full structure/agent review note:
  `reviews/2026-05-28-full-structure-agent-review.md`.
- Review finding fixes review note:
  `reviews/2026-05-29-review-finding-fixes-review.md`.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Branch: `main`
