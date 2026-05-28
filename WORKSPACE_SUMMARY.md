# Workspace Summary

Last updated: 2026-05-27

## Purpose

Birkin is a lightweight Hermes-style Python agent workspace. It provides `SKILL.md`
skill management, scoped subagent prompt packets, proposal-mode self-improvement,
local CLI/API model execution, Obsidian-backed memory, a usage ledger, Telegram
onboarding, a machine-facing gateway, and a local Web UI.

## Current State

- Python package: `src/birkin_agent`.
- Primary CLI entrypoint: `birkin-codex` via editable install. With no arguments it opens
  the Hermes-style interactive chat CLI.
- Script entrypoints: `scripts/setup`, `scripts/setup.ps1`, `scripts/birkin-codex`,
  `scripts/birkin-codex.ps1`, or `python -m birkin_agent`.
- Compatibility CLI alias: `birkin`.
- Model selection: `birkin-codex model list`, `birkin-codex model use <profile>`, and
  `birkin-codex agents run --model <profile>`.
- Setup wizard: `birkin-codex setup wizard` configures default model, Obsidian memory,
  and Telegram onboarding.
- Auth profiles: `codex-cli` delegates login/logout/status to the local Codex CLI without storing tokens.
- API profiles: `openai-compatible` and `local-compatible` support OpenAI-compatible chat completions.
- Gateway: `birkin-codex gateway run --port 8770`, serving local HTTP status/model/auth/API/run routes.
- Setup readiness: `birkin-codex setup` checks workspace, models, auth, API, gateway,
  memory, Telegram, ledger, skills, agents, and chat.
- Memory: `birkin-codex memory status|record|recall|set-vault` uses an
  Obsidian-compatible markdown vault at `memory/obsidian-vault` by default.
- Ledger: `birkin-codex ledger summary|list` reads `usage/ledger.jsonl`; every run
  appends estimated and provider token fields.
- Telegram: `birkin-codex telegram setup|status|test` stores chat id plus token env
  name, never the bot token.
- Skill config verification: `birkin-codex skills config` reports roots, discovered/enabled/gated counts,
  precedence, selection, disabled names, and Hermes/OpenClaw reflection coverage.
- Chat: `birkin-codex`, `birkin-codex chat --message ...`, and dashboard `/api/chat`
  use the `chat` agent and normal run records.
- macOS/Linux script: `scripts/birkin-codex`.
- Windows script: `scripts/birkin-codex.ps1`.
- Web UI: `birkin-codex web --port 8765`, serving a SaaS-style dashboard with jobs, result summaries,
  status, usage, warnings, models, auth, API, and gateway tabs.
- Skill roots: `skills`, `.agents/skills`, `managed-skills`, `bundled-skills`.
- Bundled native skills: 21 total; gated examples include Google Workspace and smart home.
- Hermes upstream skills: 90 `hermes-<name>` skills from upstream commit
  `2d5dcfabc312d43f87a4f0f44c45f62cf24a09b2`, with exact source mirrored under
  `skills/upstream/hermes`.
- OpenClaw upstream skills: 57 `openclaw-<name>` skills from upstream commit
  `d00e764e66555320ac75f048c2767ba5877de0a9`, with exact source mirrored under
  `skills/upstream/openclaw`.
- Default agents: planner, builder, reviewer, researcher, operator, chat.
- Chat agent skills: `memory-recall`, `taskflow`, and `documentation`.
- Default model profiles: `packet`, `codex-local`, `api-openai`, and `custom-local`.

## Verification Snapshot

- `PYTHONPATH=src; py -m unittest discover -s tests`: 18 tests passed.
- `py -m compileall -q src tests tools`: passed.
- `.venv\Scripts\python.exe -m pip install -e .`: passed.
- `scripts/setup.ps1 -SkipCheck`: installed editable package into `.venv` and created `.venv\Scripts\birkin-codex.exe`.
- `birkin-codex` with `/exit` piped on stdin: opened the interactive chat CLI and exited cleanly.
- `birkin-codex doctor`: `ok` with warnings for missing `OPENAI_API_KEY`, first-write
  Obsidian vault creation, and Telegram not enabled.
- `birkin-codex skills validate`: `ok`.
- `birkin-codex setup --json`: completed with warning status.
- `birkin-codex skills config --json`: completed; upstream mirror check reports
  147 mirrored upstream skills and 0 missing directories.
- `birkin-codex memory status --json`: passed.
- `birkin-codex ledger summary --json`: passed.
- `birkin-codex telegram status --json`: passed.
- `birkin-codex setup wizard --model packet --obsidian-vault memory/obsidian-vault --non-interactive`: passed.
- `.\scripts\birkin-codex.ps1 chat --message "hello" --model packet --json`: packet-only chat succeeded.
- `.\scripts\birkin-codex.ps1 auth list --json`: 2 auth profiles, with `codex-cli` available on PATH.
- `.\scripts\birkin-codex.ps1 api list --json`: 2 API profiles.
- `birkin-codex gateway routes`: includes memory, ledger, and Telegram status routes.
- Dashboard smoke: `http://127.0.0.1:8766/api/status` reported setup status, 9 skill
  config rows, Obsidian memory status, ledger totals, and Telegram status; served HTML
  contained chat/setup/memory/ledger/telegram tabs.
- Chat smoke: `POST http://127.0.0.1:8766/api/chat` returned packet-only status with a reply and run record.
- Gateway smoke: `http://127.0.0.1:8770/health` returned `ok`; `/api/ledger` returned ledger summary.
- `birkin-codex skills list --json`: includes native skills plus 90 Hermes and 57 OpenClaw upstream-backed skills.
- Existing compatibility scripts remain at `scripts/birkin` and `scripts/birkin.ps1`.
- Previous Playwright Web UI check: dashboard title loaded, running/completed/warning/usage metrics rendered, Run generated a job record, no console errors.
- Code review note: `reviews/2026-05-27-hermes-skills-readme-review.md`.
- Latest code review note: `reviews/2026-05-27-model-selection-review.md`.
- Current code review note: `reviews/2026-05-27-auth-api-gateway-review.md`.
- Latest code review note: `reviews/2026-05-27-setup-chat-skills-review.md`.
- Current code review note: `reviews/2026-05-28-memory-ledger-onboarding-review.md`.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Base remote state before import: `main` had a single `README.md` with `# literate-memory`.
