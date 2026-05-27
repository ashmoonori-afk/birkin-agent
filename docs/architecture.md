# Architecture

Scope date: 2026-05-27.

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
- `src/birkin_agent/improve.py`: records lessons, gathers signals, creates pending
  skill improvement proposals, and applies approved patches.
- `src/birkin_agent/dashboard.py`: turns run records, usage, warnings, agents, and
  skills into dashboard API data.
- `src/birkin_agent/web.py`: serves a local operator dashboard with running jobs,
  result summaries, status, usage, warnings, skills, agents, and job generation.
- `skills/`: bundled starter skill set covering core, tools, development, creative,
  integrations, and product workflows.

## Skill Precedence

Configured roots are checked in order:

1. `skills`
2. `.agents/skills`
3. `managed-skills`
4. `bundled-skills`

The first skill with a given `name` wins. Later duplicates are reported as shadowed.

## Safety Model

- Default runner is `dry-run`.
- Real CLI execution requires an explicit argv command in `birkin.json`.
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
