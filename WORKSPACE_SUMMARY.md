# Workspace Summary

Last updated: 2026-05-27

## Purpose

Birkin is a lightweight Hermes-style Python agent workspace. It provides `SKILL.md`
skill management, scoped subagent prompt packets, proposal-mode self-improvement, a
CLI, and a local Web UI.

## Current State

- Python package: `src/birkin_agent`.
- CLI entrypoint: `birkin` via editable install or `python -m birkin_agent`.
- macOS/Linux script: `scripts/birkin`.
- Windows script: `scripts/birkin.ps1`.
- Web UI: `birkin web --port 8765`, serving a SaaS-style dashboard at `http://127.0.0.1:8765`.
- Skill roots: `skills`, `.agents/skills`, `managed-skills`, `bundled-skills`.
- Bundled skills: 21 total; gated examples include Google Workspace and smart home.
- Default agents: planner, builder, reviewer, researcher, operator.

## Verification Snapshot

- `py -m unittest discover -s tests`: 7 tests passed.
- `py -m compileall -q src tests`: passed.
- `py -m birkin_agent doctor`: `ok`.
- `py -m birkin_agent skills validate`: `ok`.
- `.\scripts\birkin.ps1 doctor`: `ok`.
- Editable install console command `.venv\Scripts\birkin.exe doctor`: `ok`.
- Playwright Web UI check: dashboard title loaded, running/completed/warning/usage metrics rendered, Run generated a job record, no console errors.

## Git Target

- Remote: `https://github.com/ashmoonori-afk/birkin-agent.git`
- Base remote state before import: `main` had a single `README.md` with `# literate-memory`.
