from __future__ import annotations

DEFAULT_CONFIG = {
    "version": 1,
    "workspace": {
        "name": "birkin_codex",
        "summary": "WORKSPACE_SUMMARY.md",
        "promptFiles": ["AGENTS.md", "SOUL.md", "TOOLS.md"],
    },
    "skills": {
        "roots": ["skills", ".agents/skills", "managed-skills", "bundled-skills"],
        "watch": True,
        "watchDebounceMs": 250,
        "enabled": None,
        "disabled": [],
        "allowSymlinkTargets": [],
    },
    "agents": {
        "defaults": {
            "workspace": ".",
            "runner": "dry-run",
            "model": None,
            "skills": None,
            "sandbox": {"mode": "workspace-only"},
        },
        "list": [
            {
                "id": "planner",
                "role": "Break ambiguous work into evidence-backed plans.",
                "skills": ["taskflow", "memory-recall", "documentation"],
            },
            {
                "id": "builder",
                "role": "Implement code and automation inside the workspace.",
                "skills": ["shell-runtime", "filesystem", "skill-authoring", "data-analysis"],
            },
            {
                "id": "reviewer",
                "role": "Review code, plans, security, and progress before delivery.",
                "skills": ["code-review", "skill-security-audit", "documentation"],
            },
            {
                "id": "researcher",
                "role": "Collect cited evidence and prepare reusable notes.",
                "skills": ["web-research", "browser-automation", "documentation"],
            },
            {
                "id": "operator",
                "role": "Run recurring or channel-facing workflows with tight policy.",
                "skills": ["scheduling", "messaging-gateway", "subagent-orchestration"],
            },
        ],
    },
    "runners": {
        "dry-run": {
            "type": "packet",
            "description": "Build the prompt packet and save a run record without calling a model.",
        },
        "local-cli": {
            "type": "command",
            "command": [],
            "timeoutSeconds": 1800,
            "description": "Optional command adapter. Provide an argv list such as ['codex', 'exec', '-'].",
        },
    },
    "models": {
        "default": "packet",
        "profiles": {
            "packet": {
                "provider": "packet",
                "model": "packet-only",
                "runner": "dry-run",
                "command": [],
                "timeoutSeconds": 1800,
                "description": "Build prompt packets and run records without calling a model.",
            },
            "codex-local": {
                "provider": "openai-codex-cli",
                "model": "gpt-5.5",
                "runner": "local-cli",
                "command": ["codex", "exec", "--model", "{model}", "-"],
                "timeoutSeconds": 1800,
                "description": "Local Codex CLI profile. Requires `codex` on PATH and a valid local login.",
            },
            "custom-local": {
                "provider": "local-cli",
                "model": "local",
                "runner": "local-cli",
                "command": [],
                "timeoutSeconds": 1800,
                "description": "Template profile for any local model CLI. Fill command with argv strings.",
            },
        },
    },
    "improvement": {
        "mode": "proposal",
        "sources": ["runs", "reviews", "memory"],
        "signalPrefixes": ["LESSON:", "USER_CORRECTION:", "FIXME:", "TODO(skill):", "FAILED:"],
    },
}


DEFAULT_AGENT_FILES = {
    "AGENTS.md": """# Birkin Agent Workspace

## Operating Rules

1. Work inside this workspace unless the user explicitly expands scope.
2. Treat `SKILL.md` folders as procedural memory, not executable trust.
3. Keep claims tied to source files, run records, or cited external references.
4. Prefer proposal-mode self-improvement before changing skills automatically.
5. Run `birkin doctor`, `birkin skills validate`, tests, and code review after code changes.
""",
    "SOUL.md": """# Workspace Soul

Birkin is a lightweight Hermes-style local agent workspace. It favors small text
artifacts, explicit skill metadata, scoped subagents, proposal-mode self-improvement,
and auditable run records over heavyweight services.
""",
    "TOOLS.md": """# Tool Policy

The default model profile is `packet`; it generates a prompt packet and run record.
Configure `models.profiles.<id>.command` in `birkin.json` before allowing a subagent
to call an external model CLI. Keep runner commands as argv arrays, not shell strings.
""",
}


DEFAULT_SCRIPT_FILES = {
    "scripts/birkin": """#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PYTHON_BIN=${PYTHON:-python3}

if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH="$ROOT_DIR/src:$PYTHONPATH"
else
  export PYTHONPATH="$ROOT_DIR/src"
fi

exec "$PYTHON_BIN" -m birkin_agent "$@"
""",
    "scripts/birkin.ps1": """param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
)

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$SrcDir = Join-Path $RootDir "src"

if ($env:PYTHONPATH) {
  $env:PYTHONPATH = "$SrcDir;$env:PYTHONPATH"
} else {
  $env:PYTHONPATH = $SrcDir
}

py -m birkin_agent @RemainingArgs
exit $LASTEXITCODE
""",
}


REFERENCE_NOTES = r"""# Reference Notes

Scope date: 2026-05-27.

Reference snapshot:

- Hermes Agent commit: `bb4703c761ea6687b6399aa2e61e0a08fabd3ca3`
- OpenClaw commit: `8d6b5997375890608a1bb46a08c1f5a819443d59`

## Sources Used

- Hermes Agent repository: https://github.com/NousResearch/hermes-agent
- Hermes CLI commands documentation: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/cli-commands.md
- Hermes skills documentation: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md
- Hermes bundled skills catalog: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/skills-catalog.md
- OpenClaw repository: https://github.com/openclaw/openclaw
- OpenClaw skills documentation: https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md
- OpenClaw tools overview: https://github.com/openclaw/openclaw/blob/main/docs/tools/index.md

## Design Inputs Reflected

- AgentSkills-compatible `SKILL.md` folders with frontmatter.
- Progressive disclosure: list metadata first; load full bodies only when needed.
- Agent-managed skills through proposal and apply commands.
- Skill precedence with workspace roots before lower-priority roots.
- Skill gating by platform, environment variables, and required binaries.
- Per-agent skill allowlists.
- Model selection through configured provider/model profiles and per-run overrides.
- Snapshot-style prompt packets for CLI subagent execution.
- Web UI as an operator control surface, not a separate backend product.
- Self-improvement loop based on run records, reviews, memory notes, and user corrections.
- Hermes bundled skill coverage through 90 lightweight `hermes-<name>` reflection skills.
- OpenClaw skill coverage through 57 lightweight `openclaw-<name>` reflection skills.

## Boundary

This workspace reflects the referenced systems in a lightweight Python implementation.
It does not vendor either upstream project or claim API compatibility with their private
runtime internals. Reflection skills preserve source-linked capability intent, not full
upstream implementations.
"""


ARCHITECTURE_DOC = r"""# Architecture

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
- `src/birkin_agent/improve.py`: records lessons, gathers signals, creates pending
  skill improvement proposals, and applies approved patches.
- `src/birkin_agent/dashboard.py`: turns run records, usage, warnings, agents, and
  skills into dashboard API data.
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
- Real CLI execution requires an explicit model profile command in `birkin.json`
  and `--execute` on the run command.
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
"""


MACOS_DOC = r"""# macOS Usage

Scope date: 2026-05-27.

Birkin is a Python workspace and does not require Windows-specific tooling. The default
runtime uses only the Python standard library.

## Requirements

- macOS 12 or newer.
- Python 3.11 or newer.
- Git, only when committing or pulling remote work.

## Run Without Installing

```sh
cd birkin-agent
./scripts/birkin doctor
./scripts/birkin skills list
./scripts/birkin agents run planner --task "Plan the next release"
./scripts/birkin web --port 8765
```

Open `http://127.0.0.1:8765`.

## Editable Install

```sh
cd birkin-agent
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
birkin doctor
birkin skills validate
birkin web --port 8765
```

## Local CLI Runner

Birkin does not call a model by default. To connect a local CLI, choose or add a
model profile:

```sh
birkin model list
birkin model use codex-local
birkin agents run builder --model codex-local --execute --task "Implement the change"
```

To add a custom local CLI profile:

```sh
birkin model add my-local \
  --provider local-cli \
  --model local-model \
  --runner local-cli \
  --command-json '["my-model-cli","--model","{model}","-"]'
```

Keep the command as an argv array. Do not put shell pipelines or secrets in this config.
"""


DEFAULT_DASHBOARD_DOC = r"""# Dashboard

Scope date: 2026-05-27.

The Birkin Web UI is an operator dashboard, not a landing page. It is served by the
Python standard library:

```sh
birkin web --port 8765
```

Open `http://127.0.0.1:8765`.

## First Screen

- Workspace summary.
- Estimated usage from job prompt packets.
- Running jobs.
- Completed and failed job counts.
- Recent job results with status, agent, model, task, result summary, usage, and timestamp.
- Model profile count and a model selector for new jobs.
- Warnings in a separate panel.
- A job creation form that writes a dry-run record by default.

## Data Source

The dashboard reads:

- `runs/*.json` for job history, summaries, status, and usage.
- `skills/**/SKILL.md` for skill status and gating warnings.
- `birkin.json` for agents, models, runners, and allowlists.
- `memory/`, `reviews/`, and `runs/` for improvement signals.

## Warning Model

Warnings are separate from job results. They include workspace doctor warnings, skill
validation warnings, model profile warnings, agent allowlist warnings, and gated skills
such as missing environment variables or missing config.
"""


MODEL_SELECTION_DOC = r"""# Model Selection

Scope date: 2026-05-27.

Birkin uses model profiles to keep model choice separate from agent roles. The default
profile is `packet`, which never calls an external model.

## Commands

```sh
birkin model list
birkin model use packet
birkin model use codex-local
birkin agents run builder --model codex-local --execute --task "Implement the change"
```

`birkin models` is an alias for `birkin model`.

## Local CLI Profiles

Profiles live in `birkin.json` under `models.profiles`. A profile can define a local
CLI argv template. The placeholders `{model}`, `{provider}`, and `{profile}` are replaced
at run time.

```json
{
  "models": {
    "default": "packet",
    "profiles": {
      "codex-local": {
        "provider": "openai-codex-cli",
        "model": "gpt-5.5",
        "runner": "local-cli",
        "command": ["codex", "exec", "--model", "{model}", "-"],
        "timeoutSeconds": 1800
      }
    }
  }
}
```

Add a custom profile without editing JSON by hand:

```sh
birkin model add my-local \
  --provider local-cli \
  --model local-model \
  --runner local-cli \
  --command-json '["my-model-cli","--model","{model}","-"]'
```

## Safety

- Model profiles do not execute unless `birkin agents run --execute` is used.
- Commands are argv arrays, not shell strings.
- Secrets should stay in the local CLI's own auth store or environment, not in `birkin.json`.
"""


DEFAULT_DOC_FILES = {
    "docs/reference-notes.md": REFERENCE_NOTES,
    "docs/architecture.md": ARCHITECTURE_DOC,
    "docs/dashboard.md": DEFAULT_DASHBOARD_DOC,
    "docs/macos.md": MACOS_DOC,
    "docs/model-selection.md": MODEL_SELECTION_DOC,
}


README = r"""```text
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
| Model selection | Provides Hermes-style model profiles for packet-only runs, Codex CLI, or any local CLI argv template. |
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
birkin model list
birkin model use codex-local
birkin agents list
birkin agents packet planner --model packet --task "Plan the work"
birkin agents run builder --model codex-local --task "Prepare the implementation"
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
- Selectable model profiles.
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

## Model and Runner Selection

The default model profile is `packet`. It writes a run record and prompt packet without
calling a model. This mirrors the Hermes split between terminal model setup and per-run
model switching, but keeps the implementation local and inspectable.

List and choose model profiles:

```sh
birkin model list
birkin model use packet
birkin model use codex-local
```

Run with an explicit model profile:

```sh
birkin agents run builder --model codex-local --execute --task "Implement the change"
```

Configure local CLI profiles in `birkin.json`:

```json
{
  "models": {
    "default": "packet",
    "profiles": {
      "codex-local": {
        "provider": "openai-codex-cli",
        "model": "gpt-5.5",
        "runner": "local-cli",
        "command": ["codex", "exec", "--model", "{model}", "-"],
        "timeoutSeconds": 1800
      }
    }
  }
}
```

You can also add a profile from the local CLI:

```sh
birkin model add codex-fast \
  --provider openai-codex-cli \
  --model gpt-5.5 \
  --runner local-cli \
  --command-json '["codex","exec","--model","{model}","-"]'
```

Keep commands as argv arrays. Do not put shell pipelines or secrets in `birkin.json`.

## Advantages

- Lightweight: Python standard library core, no service stack required.
- Inspectable: run records, skill files, and proposals are plain text or JSON.
- Safer by default: dry-run runner, explicit `--execute`, and proposal-mode improvement.
- Portable: macOS/Linux shell script, Windows PowerShell script, and editable Python install.
- Model-profile based: switch between packet-only, Codex CLI, or a custom local CLI without code changes.
- Hermes-aware: all bundled Hermes skill directories are represented as Birkin capability markers.
- OpenClaw-aware: every upstream OpenClaw skill directory is represented as a Birkin capability marker.
- Dashboard-first operations: job status, result summaries, usage, and warnings are visible immediately.

## Tradeoffs

- Not a drop-in Hermes replacement: no built-in messaging gateway, provider setup wizard, Honcho user model, or cloud terminal backend.
- Not a drop-in OpenClaw replacement: reflection skills are routing markers unless a local adapter is implemented.
- Hermes and OpenClaw reflections are not vendored upstream implementations; they are source-linked capability maps.
- No model calls by default: you must choose a local CLI model profile and execute explicitly before real model execution.
- Usage is estimated from prompt text and run output, not provider billing APIs.
- macOS script is included, but this repository was initially verified from Windows; macOS should be tested on a real Mac before release claims beyond CLI portability.

## Reference Points

Birkin was shaped by these upstream ideas:

- Hermes README themes: self-improvement, skills, subagents, scheduled automation, model choice, and remote-friendly operation.
- Hermes model docs: terminal model setup plus per-run model override, adapted here as local CLI profiles.
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

- Unit tests: 10 passed.
- Dashboard smoke check: rendered job metrics, warnings, usage, and run action without console errors.
- Code review note: [reviews/2026-05-27-model-selection-review.md](reviews/2026-05-27-model-selection-review.md).

## More

- [Architecture](docs/architecture.md)
- [Dashboard](docs/dashboard.md)
- [macOS usage](docs/macos.md)
- [Model selection](docs/model-selection.md)
- [Hermes skill map](docs/hermes-skill-map.md)
- [OpenClaw skill map](docs/openclaw-skill-map.md)
- [Reference notes](docs/reference-notes.md)
"""
