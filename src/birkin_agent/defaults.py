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

The default runner is `dry-run`; it generates a prompt packet and run record. Configure
`runners.local-cli.command` in `birkin.json` before allowing a subagent to call an external
model CLI. Keep runner commands as argv arrays, not shell strings.
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


REFERENCE_NOTES = """# Reference Notes

Scope date: 2026-05-27.

## Sources Used

- Hermes Agent repository: https://github.com/NousResearch/hermes-agent
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
- Snapshot-style prompt packets for CLI subagent execution.
- Web UI as an operator control surface, not a separate backend product.
- Self-improvement loop based on run records, reviews, memory notes, and user corrections.

## Boundary

This workspace reflects the referenced systems in a lightweight Python implementation.
It does not vendor either upstream project, copy their full skill catalogs, or claim API
compatibility with their private runtime internals.
"""


ARCHITECTURE_DOC = """# Architecture

Scope date: 2026-05-27.

Birkin is a lightweight Python implementation of a Hermes-style agent workspace. It uses
Hermes Agent as the reference model for `SKILL.md` driven progressive disclosure and
agent-managed skill evolution, and OpenClaw as the reference model for skill precedence,
gating, operator safety, and broad bundled skill coverage.

Birkin is not a fork of either project. It does not vendor their code or claim runtime
compatibility with their private runtime internals.

## Core Pieces

- `src/birkin_agent/skills.py`: indexes AgentSkills-compatible `SKILL.md` folders.
- `src/birkin_agent/agents.py`: builds subagent prompt packets and run records.
- `src/birkin_agent/improve.py`: records lessons and manages approved skill patches.
- `src/birkin_agent/web.py`: serves the local operator Web UI.
- `skills/`: bundled starter skill set.
"""


MACOS_DOC = """# macOS Usage

Scope date: 2026-05-27.

Birkin is a Python workspace and does not require Windows-specific tooling. The default
runtime uses only the Python standard library.

## Run Without Installing

```sh
cd birkin-agent
./scripts/birkin doctor
./scripts/birkin skills list
./scripts/birkin agents run planner --task "Plan the next release"
./scripts/birkin web --port 8765
```

Open `http://127.0.0.1:8765`.
"""


DEFAULT_DASHBOARD_DOC = """# Dashboard

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
- Recent job results with status, agent, task, result summary, usage, and timestamp.
- Warnings in a separate panel.
- A job creation form that writes a dry-run record by default.
"""


DEFAULT_DOC_FILES = {
    "docs/reference-notes.md": REFERENCE_NOTES,
    "docs/architecture.md": ARCHITECTURE_DOC,
    "docs/dashboard.md": DEFAULT_DASHBOARD_DOC,
    "docs/macos.md": MACOS_DOC,
}


README = """# Birkin Agent

Birkin is a lightweight Python agent workspace in the Hermes family of ideas:
`SKILL.md` first, CLI first, subagent-ready, self-improving, and easy to run on
Windows, macOS, or Linux.

It keeps the useful primitives small:

- `SKILL.md` based skill management.
- Per-agent skill allowlists.
- CLI-first subagent prompt packets.
- Proposal-mode self-improvement.
- A built-in SaaS-style operations dashboard served by Python.
- Workspace-only path containment.

Birkin is not a fork of Hermes Agent or OpenClaw. It reflects the same direction in a
smaller Python implementation that can be inspected and changed locally.

## Quick Start: macOS and Linux

```sh
./scripts/birkin doctor
./scripts/birkin skills list
./scripts/birkin agents run planner --task "Plan the next release"
./scripts/birkin improve record --lesson "LESSON: Validate skills before running an agent." --skill skill-authoring
./scripts/birkin improve propose
./scripts/birkin web --port 8765
```

Open the Web UI at `http://127.0.0.1:8765`.

The dashboard shows running jobs, recent job results, result summaries, status, estimated
usage, enabled skills, agents, improvement signals, and warnings in separate operator
panels.

## Quick Start: Windows

```powershell
.\\scripts\\birkin.ps1 doctor
.\\scripts\\birkin.ps1 skills list
.\\scripts\\birkin.ps1 agents run planner --task "Plan the next release"
.\\scripts\\birkin.ps1 web --port 8765
```

## Editable Install

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
birkin doctor
birkin skills validate
birkin web --port 8765
```

## Skill Layout

Skills live under:

- `skills/<group>/<skill>/SKILL.md`
- `.agents/skills/<skill>/SKILL.md`
- `managed-skills/<skill>/SKILL.md`
- `bundled-skills/<skill>/SKILL.md`

Higher roots win when names conflict. A skill can include `references/`, `templates/`,
`scripts/`, and `assets/` folders, but Birkin only indexes `SKILL.md` by default.

## Runner Model

`dry-run` is the default runner. It writes a run record and prints the prompt packet. To
call a real local model CLI, edit `birkin.json`:

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

## Verification

```sh
python -m unittest discover -s tests
python -m compileall -q src tests
birkin doctor
birkin skills validate
```

Without an editable install, use `./scripts/birkin` on macOS/Linux or
`.\\scripts\\birkin.ps1` on Windows.

## More

- [Architecture](docs/architecture.md)
- [Dashboard](docs/dashboard.md)
- [macOS usage](docs/macos.md)
- [Reference notes](docs/reference-notes.md)
"""
