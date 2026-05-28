# Workspace Summary

Last updated: 2026-05-28

## Purpose

Birkin Codex is a lightweight Hermes-style Python agent workspace. It provides
`SKILL.md` skill management, scoped subagent prompt packets, local CLI/API model
execution, an OpenAI-compatible tool-calling runtime, approval-gated consequential
actions, semantic Obsidian memory, a usage ledger, Telegram onboarding/inbound polling,
Morpheus self-improvement, a machine-facing gateway, and a local SaaS-style dashboard.

## Current State

- Python package: `src/birkin_agent`.
- Primary CLI entrypoint: `birkin-codex` via editable install. With no arguments it opens
  the Hermes-style interactive chat CLI.
- Compatibility CLI alias: `birkin`.
- Script entrypoints: `scripts/setup`, `scripts/setup.ps1`, `scripts/birkin-codex`,
  `scripts/birkin-codex.ps1`, `scripts/birkin`, and `scripts/birkin.ps1`.
- Model profiles: `packet`, `codex-local`, `api-openai`, `api-agent`, and
  `custom-local`.
- Runners: packet-only `dry-run`, command-based `local-cli`, plain OpenAI-compatible
  `api`, and OpenAI-compatible `tool-agent`.
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
  warnings, models, auth, API, gateway, memory, ledger, Telegram, approvals, learning,
  reliability, Morpheus, schedules, skills, agents, setup, and chat. The learning tab can
  list, show, approve, reject, and rollback learning records through the local API.
- Skill safety: `birkin-codex skills safety` lists permission manifest, version,
  author/source, computed hash, tests, last verified, immutable status, and path.
  `skills config` now includes registry consistency and skill-safety rows.
- Setup wizard: model selection, Obsidian vault setup, Telegram onboarding, and optional
  Telegram inbound.
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

- `py -m pip install -e .`: passed. The Python script directory is not on this shell's
  PATH, so CLI smoke commands prepended the installed Scripts directory for this session.
- `py -m compileall -q src tests tools`: passed.
- `py -m unittest discover -s tests`: 29 tests passed.
- `git diff --check -- . ':!skills/upstream'`: passed.
- `birkin-codex doctor`: `ok` with expected warnings for missing `OPENAI_API_KEY` and
  Telegram not enabled.
- `birkin-codex skills validate`: `ok`.
- `birkin-codex skills config --json`: passed; upstream mirror check reports 147
  mirrored upstream skills and 0 missing directories. Registry consistency and
  skill-safety checks are `ok`.
- `birkin-codex skills safety --json`: passed.
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
- Gateway smoke on `127.0.0.1:8772`: `/health`, `/api/reliability`, and `/api/learning`
  passed, including reliability replay records.
- Code review note: `reviews/2026-05-28-verified-learning-reliability-review.md`.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Branch: `main`
