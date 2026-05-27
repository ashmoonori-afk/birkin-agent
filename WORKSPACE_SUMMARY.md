# Workspace Summary

Last updated: 2026-05-27

## Purpose

Birkin is a lightweight Hermes-style Python agent workspace. It provides `SKILL.md`
skill management, scoped subagent prompt packets, proposal-mode self-improvement,
local CLI/API model execution, a machine-facing gateway, and a local Web UI.

## Current State

- Python package: `src/birkin_agent`.
- Primary CLI entrypoint: `birkin-codex` via editable install, `scripts/birkin-codex`,
  `scripts/birkin-codex.ps1`, or `python -m birkin_agent`.
- Compatibility CLI alias: `birkin`.
- Model selection: `birkin-codex model list`, `birkin-codex model use <profile>`, and
  `birkin-codex agents run --model <profile>`.
- Auth profiles: `codex-cli` delegates login/logout/status to the local Codex CLI without storing tokens.
- API profiles: `openai-compatible` and `local-compatible` support OpenAI-compatible chat completions.
- Gateway: `birkin-codex gateway run --port 8770`, serving local HTTP status/model/auth/API/run routes.
- macOS/Linux script: `scripts/birkin-codex`.
- Windows script: `scripts/birkin-codex.ps1`.
- Web UI: `birkin-codex web --port 8765`, serving a SaaS-style dashboard with jobs, result summaries,
  status, usage, warnings, models, auth, API, and gateway tabs.
- Skill roots: `skills`, `.agents/skills`, `managed-skills`, `bundled-skills`.
- Bundled native skills: 21 total; gated examples include Google Workspace and smart home.
- Hermes reflections: 90 `hermes-<name>` capability marker skills from upstream commit `bb4703c761ea6687b6399aa2e61e0a08fabd3ca3`.
- OpenClaw reflections: 57 `openclaw-<name>` capability marker skills from upstream commit `8d6b5997375890608a1bb46a08c1f5a819443d59`.
- Default agents: planner, builder, reviewer, researcher, operator.
- Default model profiles: `packet`, `codex-local`, `api-openai`, and `custom-local`.

## Verification Snapshot

- `PYTHONPATH=src; py -m unittest discover -s tests`: 13 tests passed.
- `py -m compileall -q src tests`: passed.
- `.\scripts\birkin-codex.ps1 doctor`: `ok` with warning that `OPENAI_API_KEY` is not set for `openai-compatible`.
- `.\scripts\birkin-codex.ps1 skills validate`: `ok`.
- `.\scripts\birkin-codex.ps1 auth list --json`: 2 auth profiles, with `codex-cli` available on PATH.
- `.\scripts\birkin-codex.ps1 api list --json`: 2 API profiles.
- `.\scripts\birkin-codex.ps1 gateway routes`: 11 routes.
- Dashboard smoke: `http://127.0.0.1:8766/api/status` reported 4 models, 2 auth profiles, 2 API profiles, and the served HTML contained auth/API/gateway tabs.
- Gateway smoke: `http://127.0.0.1:8770/health` returned `ok`; `/api/models` returned 4 profiles.
- `.\scripts\birkin-codex.ps1 skills list --json`: 168 skills total, including 90 Hermes and 57 OpenClaw reflections.
- Existing compatibility scripts remain at `scripts/birkin` and `scripts/birkin.ps1`.
- Previous Playwright Web UI check: dashboard title loaded, running/completed/warning/usage metrics rendered, Run generated a job record, no console errors.
- Code review note: `reviews/2026-05-27-hermes-skills-readme-review.md`.
- Latest code review note: `reviews/2026-05-27-model-selection-review.md`.
- Current code review note: `reviews/2026-05-27-auth-api-gateway-review.md`.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Base remote state before import: `main` had a single `README.md` with `# literate-memory`.
