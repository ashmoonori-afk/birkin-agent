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
- `src/birkin_agent/models.py`: resolves Hermes-style model profiles, local CLI
  command templates, defaults, validation, and per-run overrides.
- `src/birkin_agent/auth.py`: manages local CLI OAuth/auth profiles by delegating
  login, logout, and status commands to external CLIs such as `codex`.
- `src/birkin_agent/api.py`: calls OpenAI-compatible chat completions endpoints
  through configured API profiles.
- `src/birkin_agent/gateway.py`: serves a local machine-facing HTTP gateway for
  health, status, model, auth, API, and run operations.
- `src/birkin_agent/improve.py`: records lessons, gathers signals, creates pending
  skill improvement proposals, and applies approved patches.
- `src/birkin_agent/dashboard.py`: turns run records, usage, warnings, agents, and
  skills into dashboard API data, including model, auth, API, and gateway status.
- `src/birkin_agent/web.py`: serves a local operator dashboard with running jobs,
  result summaries, status, usage, warnings, skills, agents, and job generation.
- `skills/`: bundled starter skill set covering core, tools, development, creative,
  integrations, and product workflows.
- `skills/hermes-reflections/`: one lightweight capability marker per Hermes bundled
  upstream skill directory, generated from the referenced Hermes snapshot.
- `skills/openclaw-reflections/`: one lightweight capability marker per OpenClaw
  upstream skill directory, generated from the referenced OpenClaw snapshot.

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
- Local CLI OAuth profiles call the external tool's own login store and do not write
  tokens to Birkin config.
- The gateway binds to localhost by default. If `BIRKIN_GATEWAY_TOKEN` is set, or
  `gateway.requireToken` is true, it requires a bearer token or `x-birkin-token`.
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
