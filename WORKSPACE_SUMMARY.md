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
  packet-only subagents.
- Approval gate: `birkin-codex approvals list|approve|reject`; pending approvals are
  stored under `approvals/pending` and history under `approvals/history`.
- Memory: semantic Obsidian markdown under `memory/obsidian-vault`, preserving folders
  `Birkin/Conversations`, `Birkin/Feedback`, `Birkin/Errors`, and `Birkin/Runs`.
  Notes include `kind`, `type`, `created`, `updated`, `confidence`, `sources`, `tags`,
  and Obsidian `[[wikilink]]` support.
- Ledger: `usage/ledger.jsonl` for run status, estimated tokens, provider token fields,
  and cost fields.
- Telegram: env-only bot token config, explicit test-send, and optional inbound polling.
  Runtime-requested outbound sends go through approvals.
- Morpheus: `birkin-codex morpheus --dry-run` and daemon support for the 04:00
  self-improvement review.
- Gateway: `birkin-codex gateway run --port 8770`, serving local HTTP status, model,
  auth, API, memory, ledger, Telegram, approvals, schedules, daemon, Morpheus, chat, and
  run routes. Gateway token behavior remains localhost/token based.
- Web UI: `birkin-codex web --port 8765`, showing jobs, summaries, status, usage,
  warnings, models, auth, API, gateway, memory, ledger, Telegram, approvals, Morpheus,
  schedules, skills, agents, setup, and chat.
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
- `py -m unittest discover -s tests`: 23 tests passed.
- `git diff --check -- . ':!skills/upstream'`: passed.
- `birkin-codex doctor`: `ok` with expected warnings for missing `OPENAI_API_KEY` and
  Telegram not enabled.
- `birkin-codex skills validate`: `ok`.
- `birkin-codex setup --json`: passed with warning status for optional setup items.
- `birkin-codex skills config --json`: passed; upstream mirror check reports 147
  mirrored upstream skills and 0 missing directories.
- `birkin-codex morpheus --dry-run --json`: passed and wrote a Morpheus run record.
- `birkin-codex approvals list --json`: passed.
- `birkin-codex daemon status --json`: passed.
- `birkin-codex model list --json`: shows `api-agent` using the `tool-agent` runner.
- `birkin-codex memory write-note ...` and `birkin-codex memory search Morpheus --json`:
  passed; the note includes an Obsidian wikilink.
- `birkin-codex memory status --json`: passed with one smoke note and one linked note.
- `birkin-codex ledger summary --json`: passed.
- `birkin-codex telegram status --json`: passed.
- Dashboard smoke on `127.0.0.1:8767`: status API included Morpheus and approvals; HTML
  contained `Morpheus` and did not contain the old label; `POST /api/morpheus` returned
  dry-run status.
- Gateway smoke on `127.0.0.1:8771`: `/health` returned `ok`; `POST /api/morpheus`
  returned dry-run status.
- Code review note: `reviews/2026-05-28-runtime-approval-morpheus-review.md`.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Branch: `main`
