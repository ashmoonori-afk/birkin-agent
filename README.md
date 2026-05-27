```text
██████╗ ██╗██████╗ ██╗  ██╗██╗███╗   ██╗
██╔══██╗██║██╔══██╗██║ ██╔╝██║████╗  ██║
██████╔╝██║██████╔╝█████╔╝ ██║██╔██╗ ██║
██╔══██╗██║██╔══██╗██╔═██╗ ██║██║╚██╗██║
██████╔╝██║██║  ██║██║  ██╗██║██║ ╚████║
╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
```

**The AI agent that actually remembers you.**

# Birkin Agent

Birkin is a lightweight Python agent workspace inspired by the direction of
[Hermes Agent](https://github.com/NousResearch/hermes-agent) and
[OpenClaw](https://github.com/openclaw/openclaw).

It is built for people who want the core agent-workspace primitives without installing a
full personal assistant stack: `SKILL.md` skills, scoped subagents, dry-run prompt packets,
self-improvement proposals, and a local operations dashboard.

Birkin is not a fork of Hermes Agent or OpenClaw. It does not vendor their runtime code.
It uses their public repositories as product and architecture references, then keeps the
implementation small and inspectable.

## What It Does

| Area | Birkin behavior |
| --- | --- |
| Skills | Indexes AgentSkills-style `SKILL.md` folders with metadata, precedence, validation, and gating. |
| Hermes coverage | Reflects all 90 Hermes bundled skill directories as lightweight `hermes-<name>` capability markers. |
| OpenClaw coverage | Reflects all 57 OpenClaw upstream skill directories as lightweight `openclaw-<name>` capability markers. |
| Subagents | Builds role-scoped prompt packets for planner, builder, reviewer, researcher, and operator agents. |
| Self-improvement | Records lessons, proposes skill patches, and applies approved improvements. |
| CLI | Runs as `birkin` after install, `python -m birkin_agent`, `scripts/birkin`, or `scripts/birkin.ps1`. |
| Dashboard | Shows jobs, result summaries, status, estimated usage, warnings, skills, and agents at `http://127.0.0.1:8765`. |

## Why This Exists

Hermes Agent is a broad self-improving assistant with model routing, messaging gateways,
terminal backends, memory, scheduled automation, subagents, and a full learning loop.
OpenClaw is a local-first personal assistant with many channel, app, node, canvas, and
tool skills.

Birkin takes the parts that are useful for a small agent workspace:

- Skills as procedural memory.
- Subagent prompt packets.
- Run records that can be reviewed.
- Proposal-mode learning instead of silent mutation.
- A dashboard for current jobs and warnings.
- A Python-only core that can run on macOS, Linux, or Windows.

## Quick Start

### macOS and Linux

```sh
git clone https://github.com/ashmoonori-afk/birkin-agent.git
cd birkin-agent
./scripts/birkin doctor
./scripts/birkin skills list
./scripts/birkin agents run planner --task "Plan the next release"
./scripts/birkin web --port 8765
```

### Windows PowerShell

```powershell
git clone https://github.com/ashmoonori-afk/birkin-agent.git
cd birkin-agent
.\scripts\birkin.ps1 doctor
.\scripts\birkin.ps1 skills list
.\scripts\birkin.ps1 agents run planner --task "Plan the next release"
.\scripts\birkin.ps1 web --port 8765
```

Open the dashboard:

```text
http://127.0.0.1:8765
```

## Install as a CLI

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
birkin doctor
birkin skills validate
birkin web --port 8765
```

On Windows, use `.venv\Scripts\activate` and then the same `pip install -e .` flow.

## Core Commands

```sh
birkin doctor
birkin skills list
birkin skills validate
birkin skills create release-checklist --description "Review release readiness."
birkin agents list
birkin agents packet planner --task "Plan the work"
birkin agents run builder --task "Prepare the implementation"
birkin improve record --lesson "LESSON: Validate skills before running an agent." --skill skill-authoring
birkin improve propose
birkin web --port 8765
```

## Dashboard

The Web UI is a SaaS-style operator dashboard. It is meant for repeated work, not a
marketing page.

It shows:

- Running jobs.
- Recent job results.
- Result summaries.
- Status counts.
- Estimated prompt usage.
- Enabled and gated skills.
- Agents and their skill allowlists.
- Warnings in a separate panel.

## Skill System

Skills live under:

- `skills/<group>/<skill>/SKILL.md`
- `.agents/skills/<skill>/SKILL.md`
- `managed-skills/<skill>/SKILL.md`
- `bundled-skills/<skill>/SKILL.md`

Earlier roots win when names conflict. A skill may include `references/`, `templates/`,
`scripts/`, and `assets/`, but Birkin indexes only `SKILL.md` by default.

Birkin ships with:

- Core skills for skill authoring, memory recall, subagents, and self-improvement.
- Tool skills for filesystem, shell, web research, browser automation, scheduling, and messaging gateways.
- Development skills for code review, GitHub, documentation, data analysis, and security audit.
- Creative and integration skills.
- 90 Hermes bundled skill reflections under `skills/hermes-reflections/`.
- 57 OpenClaw reflection skills under `skills/openclaw-reflections/`.

See [Hermes Skill Reflection Map](docs/hermes-skill-map.md) and
[OpenClaw Skill Reflection Map](docs/openclaw-skill-map.md).

## Runner Model

The default runner is `dry-run`. It writes a run record and prompt packet without calling
a model.

To connect a local model CLI, edit `birkin.json`:

```json
{
  "runners": {
    "local-cli": {
      "type": "command",
      "command": ["codex", "exec", "-"],
      "timeoutSeconds": 1800
    }
  }
}
```

Then run:

```sh
birkin agents run builder --runner local-cli --execute --task "Implement the change"
```

Keep runner commands as argv arrays. Do not put shell pipelines or secrets in `birkin.json`.

## Advantages

- Lightweight: Python standard library core, no service stack required.
- Inspectable: run records, skill files, and proposals are plain text or JSON.
- Safer by default: dry-run runner, explicit `--execute`, and proposal-mode improvement.
- Portable: macOS/Linux shell script, Windows PowerShell script, and editable Python install.
- Hermes-aware: all bundled Hermes skill directories are represented as Birkin capability markers.
- OpenClaw-aware: every upstream OpenClaw skill directory is represented as a Birkin capability marker.
- Dashboard-first operations: job status, result summaries, usage, and warnings are visible immediately.

## Tradeoffs

- Not a drop-in Hermes replacement: no built-in messaging gateway, provider setup wizard, Honcho user model, or cloud terminal backend.
- Not a drop-in OpenClaw replacement: reflection skills are routing markers unless a local adapter is implemented.
- Hermes and OpenClaw reflections are not vendored upstream implementations; they are source-linked capability maps.
- No model calls by default: you must configure a runner command before real model execution.
- Usage is estimated from prompt text and run output, not provider billing APIs.
- macOS script is included, but this repository was initially verified from Windows; macOS should be tested on a real Mac before release claims beyond CLI portability.

## Reference Points

Birkin was shaped by these upstream ideas:

- Hermes README themes: self-improvement, skills, subagents, scheduled automation, model choice, and remote-friendly operation.
- Hermes skills docs: `SKILL.md` as procedural memory with progressive disclosure.
- Hermes `skills/`: 90 bundled skill directories reflected as Birkin capability markers.
- OpenClaw README themes: local-first workspace, multi-agent routing, security defaults, channels, canvas, and skills.
- OpenClaw `skills/`: 57 upstream skill directories reflected as Birkin capability markers.

Local reference notes are in [docs/reference-notes.md](docs/reference-notes.md).

## Verification

```sh
python -m unittest discover -s tests
python -m compileall -q src tests
birkin doctor
birkin skills validate
```

Current snapshot:

- Unit tests: 8 passed.
- Dashboard smoke check: rendered job metrics, warnings, usage, and run action without console errors.
- Code review note: [reviews/2026-05-27-hermes-skills-readme-review.md](reviews/2026-05-27-hermes-skills-readme-review.md).

## More

- [Architecture](docs/architecture.md)
- [Dashboard](docs/dashboard.md)
- [macOS usage](docs/macos.md)
- [Hermes skill map](docs/hermes-skill-map.md)
- [OpenClaw skill map](docs/openclaw-skill-map.md)
- [Reference notes](docs/reference-notes.md)
