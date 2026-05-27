# Workspace Summary

Last updated: 2026-05-27

## Purpose

Birkin is a lightweight Hermes-style Python agent workspace. It provides `SKILL.md`
skill management, scoped subagent prompt packets, proposal-mode self-improvement, a
CLI, and a local Web UI.

## Current State

- Python package: `src/birkin_agent`.
- CLI entrypoint: `birkin` via editable install or `python -m birkin_agent`.
- Model selection: `birkin model list`, `birkin model use <profile>`, and `agents run --model <profile>`.
- macOS/Linux script: `scripts/birkin`.
- Windows script: `scripts/birkin.ps1`.
- Web UI: `birkin web --port 8765`, serving a SaaS-style dashboard at `http://127.0.0.1:8765`.
- Skill roots: `skills`, `.agents/skills`, `managed-skills`, `bundled-skills`.
- Bundled native skills: 21 total; gated examples include Google Workspace and smart home.
- Hermes reflections: 90 `hermes-<name>` capability marker skills from upstream commit `bb4703c761ea6687b6399aa2e61e0a08fabd3ca3`.
- OpenClaw reflections: 57 `openclaw-<name>` capability marker skills from upstream commit `8d6b5997375890608a1bb46a08c1f5a819443d59`.
- Default agents: planner, builder, reviewer, researcher, operator.
- Default model profiles: `packet`, `codex-local`, and `custom-local`.

## Verification Snapshot

- `PYTHONPATH=src; py -m unittest discover -s tests`: 10 tests passed.
- `py -m compileall -q src tests`: passed.
- `.\scripts\birkin.ps1 doctor`: `ok`.
- `.\scripts\birkin.ps1 skills validate`: `ok`.
- `.\scripts\birkin.ps1 skills list --json`: 168 skills total, including 90 Hermes and 57 OpenClaw reflections.
- Editable install console command `.venv\Scripts\birkin.exe doctor`: `ok`.
- Playwright Web UI check: dashboard title loaded, running/completed/warning/usage metrics rendered, Run generated a job record, no console errors.
- Code review note: `reviews/2026-05-27-hermes-skills-readme-review.md`.
- Latest code review note: `reviews/2026-05-27-model-selection-review.md`.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Base remote state before import: `main` had a single `README.md` with `# literate-memory`.
