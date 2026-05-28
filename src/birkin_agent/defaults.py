from __future__ import annotations

from .presets import LITE_SKILLS

DEFAULT_CONFIG = {
    "version": 1,
    "experience": {
        "mode": "lite",
    },
    "workspace": {
        "name": "birkin_codex",
        "summary": "WORKSPACE_SUMMARY.md",
        "promptFiles": ["AGENTS.md", "SOUL.md", "TOOLS.md"],
    },
    "skills": {
        "roots": ["skills", ".agents/skills", "managed-skills", "bundled-skills"],
        "watch": True,
        "watchDebounceMs": 250,
        "enabled": list(LITE_SKILLS),
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
            {
                "id": "chat",
                "role": "Handle interactive user chat with workspace memory and skill-aware routing.",
                "skills": ["memory-recall", "taskflow", "documentation"],
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
        "api": {
            "type": "api",
            "profile": "openai-compatible",
            "timeoutSeconds": 1800,
            "description": "OpenAI-compatible chat completions API adapter.",
        },
        "tool-agent": {
            "type": "tool-agent",
            "profile": "openai-compatible",
            "timeoutSeconds": 1800,
            "maxTurns": 8,
            "description": "OpenAI-compatible tool-calling agent runtime with approval-gated consequential tools.",
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
            "api-openai": {
                "provider": "openai-compatible",
                "model": "gpt-5.5",
                "runner": "api",
                "apiProfile": "openai-compatible",
                "command": [],
                "timeoutSeconds": 1800,
                "description": "OpenAI-compatible API profile. Requires OPENAI_API_KEY when using the default endpoint.",
            },
            "api-agent": {
                "provider": "openai-compatible",
                "model": "gpt-5.5",
                "runner": "tool-agent",
                "apiProfile": "openai-compatible",
                "command": [],
                "timeoutSeconds": 1800,
                "description": "OpenAI-compatible tool-calling agent profile with approval-gated shell, web, Telegram, and scheduling actions.",
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
    "auth": {
        "profiles": {
            "codex-cli": {
                "type": "local-cli-oauth",
                "provider": "openai-codex-cli",
                "binary": "codex",
                "loginCommand": ["codex", "login"],
                "logoutCommand": ["codex", "logout"],
                "statusCommand": ["codex", "doctor"],
                "required": False,
                "description": "Delegates OAuth/login state to the local Codex CLI without storing tokens in Birkin.",
            },
            "custom-cli": {
                "type": "local-cli-oauth",
                "provider": "local-cli",
                "binary": "",
                "loginCommand": [],
                "logoutCommand": [],
                "statusCommand": [],
                "required": False,
                "description": "Template for another OAuth-capable local CLI.",
            },
        },
    },
    "api": {
        "profiles": {
            "openai-compatible": {
                "type": "openai-compatible",
                "baseUrl": "https://api.openai.com/v1",
                "apiKeyEnv": "OPENAI_API_KEY",
                "chatPath": "/chat/completions",
                "timeoutSeconds": 1800,
                "description": "OpenAI-compatible chat completions endpoint.",
            },
            "local-compatible": {
                "type": "openai-compatible",
                "baseUrl": "http://127.0.0.1:1234/v1",
                "apiKeyEnv": "",
                "chatPath": "/chat/completions",
                "timeoutSeconds": 1800,
                "description": "Template for a local OpenAI-compatible server.",
            },
        },
    },
    "gateway": {
        "host": "127.0.0.1",
        "port": 8770,
        "tokenEnv": "BIRKIN_GATEWAY_TOKEN",
        "requireToken": False,
    },
    "memory": {
        "provider": "obsidian",
        "vaultPath": "memory/obsidian-vault",
        "allowExternalVault": False,
        "folders": {
            "conversations": "Birkin/Conversations",
            "feedback": "Birkin/Feedback",
            "errors": "Birkin/Errors",
            "runs": "Birkin/Runs",
            "user": "Birkin/User",
            "project": "Birkin/Project",
            "environment": "Birkin/Environment",
            "workflow": "Birkin/Workflow",
            "ephemeral": "Birkin/Ephemeral",
            "negative": "Birkin/Negative",
        },
        "autoCapture": {"chat": True, "runs": True, "feedback": True, "errors": True},
        "historyPath": "memory/history.jsonl",
        "negativeRevalidateDays": 30,
    },
    "telegram": {
        "enabled": False,
        "botTokenEnv": "TELEGRAM_BOT_TOKEN",
        "chatId": "",
        "parseMode": "",
        "inboundEnabled": False,
        "lastUpdateId": 0,
    },
    "approvals": {
        "autoApprove": ["memory", "skills"],
        "pendingPath": "approvals/pending",
        "historyPath": "approvals/history",
        "riskTiers": {
            "memory": "safe",
            "skills": "review",
            "file": "review",
            "shell": "dangerous",
            "external": "external",
            "telegram": "external",
            "schedule": "review",
            "cron": "review",
            "mail": "external",
            "calendar": "external",
            "payment": "irreversible",
            "delete": "irreversible",
        },
    },
    "learning": {
        "eventsPath": "learning/events.jsonl",
        "pendingPath": "learning/proposals/pending",
        "historyPath": "learning/proposals/history",
        "safeConfidence": 0.85,
    },
    "reliability": {
        "eventsPath": "reliability/events.jsonl",
        "budgets": {
            "perRunTokenLimit": 120000,
            "dailyTokenLimit": 500000,
            "monthlyTokenLimit": 5000000,
            "warnAtPct": 80,
        },
    },
    "morpheus": {
        "enabled": False,
        "hour": 4,
        "minute": 0,
        "timezone": "local",
        "dryRun": True,
    },
    "scheduler": {
        "path": "schedules/jobs.json",
        "statusPath": "schedules/daemon-status.json",
    },
    "ledger": {
        "path": "usage/ledger.jsonl",
        "currency": "USD",
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
5. Run `birkin-codex doctor`, `birkin-codex skills validate`, tests, and code review after code changes.
""",
    "SOUL.md": """# Workspace Soul

Birkin is a lightweight Hermes-style local agent workspace. It favors small text
artifacts, explicit skill metadata, scoped subagents, proposal-mode self-improvement,
and auditable run records over heavyweight services.
""",
    "TOOLS.md": """# Tool Policy

The default model profile is `packet`; it generates a prompt packet and run record.
Configure a local CLI command or API profile in `birkin.json` before allowing a subagent
to call an external model. Keep runner commands as argv arrays, not shell strings.
Store secrets in the local CLI auth store or environment variables, not in `birkin.json`.
""",
}


DEFAULT_SCRIPT_FILES = {
    "scripts/install.sh": """#!/usr/bin/env sh
# Birkin Codex one-line installer for macOS, Linux, and WSL.
#
#   curl -fsSL https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.sh | sh
#
# Installs the `birkin-codex` command with uv, pipx, or pip --user.
set -eu

REPO="${BIRKIN_REPO:-https://github.com/ashmoonori-afk/birkin-agent}"
REF="${BIRKIN_REF:-main}"
SPEC="git+${REPO}@${REF}"

printf '==> Installing birkin-codex from %s\\n' "$SPEC"

if command -v uv >/dev/null 2>&1; then
  printf '    using uv\\n'
  uv tool install --force "$SPEC"
elif command -v pipx >/dev/null 2>&1; then
  printf '    using pipx\\n'
  pipx install --force "$SPEC"
elif command -v python3 >/dev/null 2>&1; then
  printf '    using pip --user\\n'
  python3 -m pip install --user --upgrade "$SPEC"
else
  printf '!! Need one of: uv, pipx, or python3. Install Python 3.11+ first.\\n' >&2
  exit 1
fi

printf '\\n==> Done. Start here:\\n'
printf '    birkin-codex setup wizard\\n'
printf '    birkin-codex\\n'
printf '    birkin-codex web --port 8765\\n'
printf '\\n'
if ! command -v birkin-codex >/dev/null 2>&1; then
  printf 'Note: if birkin-codex is not found, add your tool bin directory to PATH.\\n'
  printf '      Common locations: ~/.local/bin, pipx bin path, or uv tool dir.\\n'
fi
""",
    "scripts/install.ps1": """# Birkin Codex one-line installer for Windows PowerShell.
#
#   irm https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.ps1 | iex
#
# Installs the `birkin-codex` command with uv, pipx, or pip --user.
$ErrorActionPreference = "Stop"

$Repo = if ($env:BIRKIN_REPO) { $env:BIRKIN_REPO } else { "https://github.com/ashmoonori-afk/birkin-agent" }
$Ref = if ($env:BIRKIN_REF) { $env:BIRKIN_REF } else { "main" }
$Spec = "git+$Repo@$Ref"

Write-Host "==> Installing birkin-codex from $Spec"

function Have($Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (Have "uv") {
  Write-Host "    using uv"
  uv tool install --force $Spec
} elseif (Have "pipx") {
  Write-Host "    using pipx"
  pipx install --force $Spec
} elseif (Have "python") {
  Write-Host "    using pip --user"
  python -m pip install --user --upgrade $Spec
} elseif (Have "py") {
  Write-Host "    using pip --user"
  py -3.11 -m pip install --user --upgrade $Spec
  if ($LASTEXITCODE -ne 0) {
    py -m pip install --user --upgrade $Spec
  }
} else {
  Write-Error "Need one of: uv, pipx, python, or py. Install Python 3.11+ first."
  exit 1
}

Write-Host ""
Write-Host "==> Done. Start here:"
Write-Host "    birkin-codex setup wizard"
Write-Host "    birkin-codex"
Write-Host "    birkin-codex web --port 8765"
if (-not (Have "birkin-codex")) {
  Write-Host ""
  Write-Host "Note: if birkin-codex is not found, add your Python/uv/pipx Scripts directory to PATH."
}
""",
    "scripts/setup": """#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN=${PYTHON:-python3}

if [ ! -x "$VENV_DIR/bin/python" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install -e "$ROOT_DIR"

if [ "${BIRKIN_SKIP_SETUP_CHECK:-0}" != "1" ]; then
  "$VENV_DIR/bin/birkin-codex" setup
fi

printf '\\nBirkin Codex is installed in .venv.\\n'
printf 'For this terminal, run:\\n'
printf '  source .venv/bin/activate\\n'
printf 'Then start the Hermes-style chat CLI with:\\n'
printf '  birkin-codex\\n'
""",
    "scripts/setup.ps1": """param(
  [switch]$SkipCheck
)

$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvDir = Join-Path $RootDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\\python.exe"
$BirkinExe = Join-Path $VenvDir "Scripts\\birkin-codex.exe"

if (-not (Test-Path $PythonExe)) {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    & py -3.11 -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
      & py -m venv $VenvDir
    }
  } else {
    & python -m venv $VenvDir
  }
}

& $PythonExe -m pip install -e $RootDir
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

if (-not $SkipCheck) {
  & $BirkinExe setup
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

Write-Host ""
Write-Host "Birkin Codex is installed in .venv."
Write-Host "For this terminal, run:"
Write-Host "  . .\\.venv\\Scripts\\Activate.ps1"
Write-Host "Then start the Hermes-style chat CLI with:"
Write-Host "  birkin-codex"
""",
    "scripts/birkin-codex": """#!/usr/bin/env sh
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
    "scripts/birkin-codex.ps1": """param(
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

Scope date: 2026-05-28.

Birkin is a lightweight Python implementation of a Hermes-style agent workspace. It uses
Hermes Agent as the reference model for `SKILL.md` driven progressive disclosure and
agent-managed skill evolution, and OpenClaw as the reference model for skill precedence,
gating, operator safety, and broad bundled skill coverage.

Birkin is now positioned as a lite-first verified-learning agent workspace: first-run
chat works in packet mode, advanced operator controls are available when needed, memory
and skill changes are evidence-gated, consequential actions are approval-first, and
runtime health is visible through the local dashboard.

The lite core is intentionally standard-library-only at runtime. `pyproject.toml`
keeps `project.dependencies` empty, and setup/doctor checks verify that policy.

Birkin is not a fork of either project. It does not vendor their code or claim runtime
compatibility with their private internals.

## Core Pieces

- `src/birkin_agent/skills.py`: indexes AgentSkills-compatible `SKILL.md` folders,
  frontmatter, precedence, enablement, and OpenClaw-style gates.
- `src/birkin_agent/agents.py`: builds subagent prompt packets with per-agent skill
  allowlists, Birkin identity, memory digest, and routed skill context, then writes
  auditable run records.
- `src/birkin_agent/models.py`: resolves Hermes-style model profiles, local CLI
  command templates, defaults, validation, and per-run overrides.
- `src/birkin_agent/auth.py`: manages local CLI OAuth/auth profiles by delegating
  login, logout, and status commands to external CLIs such as `codex`.
- `src/birkin_agent/api.py`: calls OpenAI-compatible chat completions endpoints
  through configured API profiles.
- `src/birkin_agent/runtime_deps.py`: validates the zero-runtime-dependency policy for
  the lite core.
- `src/birkin_agent/chat.py`: builds chat-mode tasks and writes normal run records
  through the selected agent and model profile.
- `src/birkin_agent/setup.py`: produces Hermes-style setup checks across workspace,
  models, auth, API, gateway, skills, agents, and chat.
- `src/birkin_agent/gateway.py`: serves a local machine-facing HTTP gateway for
  health, status, model, auth, API, setup, skill config, chat, and run operations.
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

## Prompt Packets

Every run builds a prompt packet with named sections:

1. Birkin identity and safety boundary.
2. Workspace prompt files such as `AGENTS.md`, `SOUL.md`, and `TOOLS.md`.
3. Obsidian memory digest from keyword recall.
4. Compact skill catalog with names, descriptions, and locations.
5. The user task.
6. Routed skill bodies when requested, and always for local CLI runners.

Local CLI runners therefore receive Birkin identity, memory, and skills through stdin
instead of a bare task string. Birkin still does not try to control the local CLI's
internal tool loop; it gives the CLI enough context to act as Birkin while preserving the
CLI's own auth store and tools.

Debug commands:

```sh
birkin-codex agents packet chat --task "Explain this repo" --format summary
birkin-codex agents packet chat --task "Explain this repo" --format prompt
birkin-codex chat --dry-run --message "Explain this repo"
```

## Skill Precedence

Configured roots are checked in order:

1. `skills`
2. `.agents/skills`
3. `managed-skills`
4. `bundled-skills`

The first skill with a given `name` wins. Later duplicates are reported as shadowed.

Skill discovery is hot-reload friendly: the cache key includes `SKILL.md` mtimes and the
enabled/disabled selection state, so edited skills are rediscovered without a process
restart. `birkin-codex skills sync` is a non-mutating status command for the repo-managed
Hermes/OpenClaw exact mirrors; mirrored upstream files stay immutable and attribution is
preserved.

## Safety Model

- Default runner is `dry-run`.
- Default model profile is `packet`, which never calls an external model.
- Default experience mode is `lite`, which enables a 15-skill core allowlist and hides
  advanced dashboard tabs. `birkin-codex mode use full` restores all eligible skills and
  the full operator surface.
- The lite runtime dependency policy is checked from `pyproject.toml`; non-empty
  `project.dependencies` is treated as a setup/doctor error.
- Real CLI or API execution requires an explicit model profile in `birkin.json`
  and `--execute` on the run command.
- Local CLI OAuth profiles call the external tool's own login store and do not write
  tokens to Birkin config.
- The gateway binds to localhost by default. If `BIRKIN_GATEWAY_TOKEN` is set, or
  `gateway.requireToken` is true, it requires a bearer token or `x-birkin-token`.
- Chat uses the same `--execute` safety boundary as other agent runs.
- `skills config` verifies root, enabled/disabled, gated, precedence, and reflection
  coverage in addition to `SKILL.md` validation.
- Skills are procedural memory, not executable trust.
- Web UI escapes workspace-provided table values before rendering.
- Runtime artifacts live under ignored workspace directories.

## Verification Gates

```sh
python -m unittest discover -s tests
python -m compileall -q src tests
python -m birkin_agent doctor
python -m birkin_agent skills validate
```"""


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
./scripts/birkin-codex doctor
./scripts/birkin-codex skills list
./scripts/birkin-codex agents run planner --task "Plan the next release"
./scripts/birkin-codex web --port 8765
```

Open `http://127.0.0.1:8765`.

## Hermes-Style Setup

One-line install:

```sh
curl -fsSL https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.sh | sh
birkin-codex
```

Editable source setup:

```sh
cd birkin-agent
./scripts/setup
source .venv/bin/activate
birkin-codex
```

## Editable Install

```sh
cd birkin-agent
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
birkin-codex
birkin-codex doctor
birkin-codex setup
birkin-codex skills validate
birkin-codex skills config
birkin-codex web --port 8765
```

## Local CLI Runner

Birkin does not call a model by default. To connect a local CLI, choose or add a
model profile:

```sh
birkin-codex model list
birkin-codex model use codex-local
birkin-codex agents run builder --model codex-local --execute --task "Implement the change"
```

To add a custom local CLI profile:

```sh
birkin-codex model add my-local \
  --provider local-cli \
  --model local-model \
  --runner local-cli \
  --command-json '["my-model-cli","--model","{model}","-"]'
```

Keep the command as an argv array. Do not put shell pipelines or secrets in this config.

## Auth, API, and Gateway

Local CLI auth delegates login state to the installed tool:

```sh
birkin-codex auth list
birkin-codex auth login codex-cli
```

API profiles can call OpenAI-compatible endpoints:

```sh
export OPENAI_API_KEY=...
birkin-codex agents run builder --model api-openai --execute --task "Draft the change"
```

Run the local machine-facing gateway:

```sh
birkin-codex gateway run --port 8770
```

Chat through the default packet-only profile:

```sh
birkin-codex
birkin-codex chat --message "Summarize this workspace" --model packet
```

Inside interactive chat, `/live` selects `api-agent` when `OPENAI_API_KEY` is present
or `codex-local` when the local `codex` CLI is available.
"""


DEFAULT_DASHBOARD_DOC = r"""# Dashboard

Scope date: 2026-05-28.

The Birkin Web UI is a chat-first dashboard, not a landing page. It is served by the
Python standard library:

```sh
birkin-codex web --port 8765
```

Open `http://127.0.0.1:8765`.

## First Screen

In lite mode, the navigation emphasizes Dashboard, Chat, Setup, Jobs, Memory, Skills,
and Warnings. Advanced sections are still available behind the `Show Advanced` toggle,
or permanently by switching the workspace to full mode with `birkin-codex mode use full`.

- Workspace summary.
- Estimated usage from job prompt packets.
- Running jobs.
- Completed and failed job counts.
- Recent job results with status, agent, model, task, result summary, usage, and timestamp.
- Model profile count and a model selector for new jobs.
- Memory status and durable notes.
- Setup and skill config tabs for readiness verification.
- Chat tab for message-oriented agent runs.
- Warnings in a separate panel.
- A `Try Safe Packet` form that writes a packet-only run record by default. The execute
  checkbox is an advanced control, so the first screen stays packet-safe.

Advanced mode adds auth, API, gateway, ledger, Telegram, approvals, verified learning,
reliability, Morpheus, schedules, daemon status, agent administration, and runner
execution controls.

## Data Source

The dashboard reads:

- `runs/*.json` for job history, summaries, status, and usage.
- `usage/ledger.jsonl` for ledger totals and recent usage rows.
- The configured Obsidian vault for memory status.
- `skills/**/SKILL.md` for skill status and gating warnings.
- `birkin.json` for agents, models, runners, auth profiles, API profiles, gateway
  config, and allowlists.
- `/api/chat` for chat messages through the selected agent and model profile.
- `/api/approvals` for approval list/approve/reject actions.
- `/api/learning` for learning proposal list/approve/reject actions.
- `learning/events.jsonl` and `learning/proposals/` for verified-learning state.
- `reliability/events.jsonl` for trace, delivery, and reliability log rows.
- `/api/morpheus` for manual Morpheus dry-runs from the dashboard.
- `/api/status` for setup and skill config status shown in the dashboard tabs.
- `memory/`, `reviews/`, and `runs/` for improvement signals.

## Warning Model

Warnings are separate from job results. In lite mode, optional auth/API/gateway/Telegram
warnings are hidden so first-run success is not blocked by integrations the user has not
chosen yet. Full mode and `birkin-codex doctor --advanced` include those warnings.

Visible warnings include workspace doctor warnings, skill validation warnings, model
profile warnings, pending approvals, pending learning proposals, budget warnings,
delivery failures, agent allowlist warnings, and enabled gated skills such as missing
environment variables or missing config.

## Advanced Sections

The advanced sections answer operational questions quickly:

- What is running now?
- What did the latest job return?
- Which action needs approval?
- Which learning proposal would change memory or skills?
- Did Telegram, gateway, Morpheus, memory, ledger, model/API profiles, or delivery fail?
- How close is the workspace to configured per-run, daily, or monthly token budgets?"""


MODEL_SELECTION_DOC = r"""# Model Selection

Scope date: 2026-05-28.

Birkin uses model profiles to keep model choice separate from agent roles. The default
profile is `packet`, which never calls an external model.

## Commands

```sh
birkin-codex model list
birkin-codex model use packet
birkin-codex model use codex-local
birkin-codex model use api-openai
birkin-codex agents run builder --model codex-local --execute --task "Implement the change"
```

`birkin-codex models` is an alias for `birkin-codex model`.

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
birkin-codex model add my-local \
  --provider local-cli \
  --model local-model \
  --runner local-cli \
  --command-json '["my-model-cli","--model","{model}","-"]'
```

When a local CLI profile executes, Birkin does not send a bare task string. It builds a
prompt packet containing:

- Birkin identity and safety boundaries.
- Workspace prompt files.
- Obsidian memory digest for the task.
- Compact skill catalog.
- Routed skill bodies, including upstream mirror bodies when applicable.
- The task.

This keeps Codex, Claude, or another configured CLI acting as Birkin while still letting
that CLI use its own login store and internal tool loop.

Inspect the exact packet before running a model:

```sh
birkin-codex agents packet builder --model codex-local --task "Plan a refactor" --format summary
birkin-codex agents packet builder --model codex-local --task "Plan a refactor" --format prompt
```

## API Profiles

API model profiles use the `api` runner and point at an API profile with `apiProfile`:

```json
{
  "models": {
    "profiles": {
      "api-openai": {
        "provider": "openai-compatible",
        "model": "gpt-5.5",
        "runner": "api",
        "apiProfile": "openai-compatible",
        "command": [],
        "timeoutSeconds": 1800
      }
    }
  }
}
```

Add a local OpenAI-compatible endpoint and model profile:

```sh
birkin-codex api add local-dev \
  --base-url http://127.0.0.1:1234/v1 \
  --chat-path /chat/completions

birkin-codex model add local-api \
  --provider local-dev \
  --model local-model \
  --runner api \
  --api-profile local-dev
```

## Safety

- Model profiles do not execute unless `birkin-codex agents run --execute` is used.
- Commands are argv arrays, not shell strings.
- Secrets should stay in the local CLI's own auth store or environment, not in `birkin.json`.
- API keys are read from environment variables such as `OPENAI_API_KEY`.
- `birkin-codex chat --dry-run` and `agents packet --format prompt` make zero model
  calls and are the preferred debugging path for prompt packets."""


AUTH_API_GATEWAY_DOC = r"""# Auth, API, and Gateway

Scope date: 2026-05-27.

Birkin supports three Hermes-style integration paths while keeping the default runner
safe and local:

- Local CLI auth profiles delegate OAuth/login state to a tool such as `codex`.
- API profiles call OpenAI-compatible chat completions endpoints.
- The gateway exposes a local HTTP control surface for status, model lists, auth status,
  and run creation.

## Local CLI Auth

Birkin does not store OAuth tokens. The default `codex-cli` auth profile calls the local
Codex CLI login, logout, and status commands:

```sh
birkin-codex auth list
birkin-codex auth status codex-cli
birkin-codex auth login codex-cli
birkin-codex auth logout codex-cli
```

The profile lives in `birkin.json` under `auth.profiles.codex-cli`:

```json
{
  "type": "local-cli-oauth",
  "provider": "openai-codex-cli",
  "binary": "codex",
  "loginCommand": ["codex", "login"],
  "logoutCommand": ["codex", "logout"],
  "statusCommand": ["codex", "doctor"]
}
```

Add another OAuth-capable local CLI profile:

```sh
birkin-codex auth add my-cli \
  --provider local-cli \
  --binary my-cli \
  --login-json '["my-cli","login"]' \
  --logout-json '["my-cli","logout"]' \
  --status-json '["my-cli","status"]'
```

Commands are argv arrays. Do not put shell pipelines, token strings, or secrets in
`birkin.json`.

## API Profiles

API profiles target OpenAI-compatible chat completions APIs. The default
`openai-compatible` profile uses `https://api.openai.com/v1` and reads the key from
`OPENAI_API_KEY`.

```sh
birkin-codex api list
birkin-codex model use api-openai
birkin-codex agents run builder --model api-openai --execute --task "Draft the change"
```

For a local server:

```sh
birkin-codex api add local-dev \
  --base-url http://127.0.0.1:1234/v1 \
  --chat-path /chat/completions

birkin-codex model add local-api \
  --provider local-dev \
  --model local-model \
  --runner api \
  --api-profile local-dev
```

The API runner sends one user message containing the built Birkin prompt packet. It
extracts `choices[0].message.content` when the response uses the standard chat
completions shape.

## Gateway

The gateway is a local machine-facing API. It is separate from the dashboard UI.

```sh
birkin-codex gateway routes
birkin-codex gateway status
birkin-codex gateway run --port 8770
```

Default URL:

```text
http://127.0.0.1:8770
```

Routes:

```text
GET /health
GET /routes
GET /api/status
GET /api/models
GET /api/auth
GET /api/api-profiles
GET /api/gateway
GET /api/setup
GET /api/skills/config
POST /api/run
POST /api/chat
POST /api/auth/{profile}/status
POST /api/auth/{profile}/login
POST /api/auth/{profile}/logout
```

Create a packet-only run through the gateway:

```sh
curl -s http://127.0.0.1:8770/api/run \
  -H 'content-type: application/json' \
  -d '{"agent":"planner","model":"packet","task":"Plan the next step"}'
```

Set `"execute": true` to allow the selected runner to execute. The same `--execute`
safety boundary used by the CLI is preserved in the gateway request body.

## Token Gate

By default, the gateway binds to `127.0.0.1` without requiring a token. If
`BIRKIN_GATEWAY_TOKEN` is set, or if `gateway.requireToken` is true, requests must include
one of these headers:

```text
Authorization: Bearer <token>
x-birkin-token: <token>
```

If the gateway is configured for a non-localhost host without token auth, `birkin-codex doctor`
reports a warning."""


SETUP_CHAT_SKILLS_DOC = r"""# Setup, Chat, and Skill Config

Scope date: 2026-05-28.

Birkin includes Hermes-style setup checks, an interactive chat surface, and skill
configuration verification.

## One-Line Install

macOS, Linux, and WSL:

```sh
curl -fsSL https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.sh | sh
birkin-codex
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.ps1 | iex
birkin-codex
```

The installer uses `uv`, `pipx`, or `pip --user`, whichever is available. The
source checkout still supports `scripts/setup` and `scripts/setup.ps1` for editable
local development.

## Setup Check

Run the setup check before using real model execution:

```sh
birkin-codex setup
birkin-codex setup --json
birkin-codex setup check
birkin-codex setup wizard
```

The default setup report runs in lite mode. It checks:

- Runtime dependency policy.
- Workspace files and prompt files.
- Model profiles.
- Obsidian memory.
- Skill validation.
- Agent allowlists.
- Chat agent availability.

Advanced setup checks are available when the user is ready to connect integrations:

```sh
birkin-codex setup --advanced
birkin-codex doctor --advanced
birkin-codex mode use full
```

Advanced checks add local CLI auth profiles, OpenAI-compatible API profiles, gateway
config, Telegram onboarding, approval queues, Morpheus, schedules, and usage ledger
status. `OPENAI_API_KEY` is reported as a warning only in advanced/full checks when the
default OpenAI-compatible API profile is configured but the environment variable is not
set.

## Experience Mode

Birkin starts in `lite` mode:

```sh
birkin-codex mode status
birkin-codex mode use full
birkin-codex mode use lite
```

`lite` mode keeps a 15-skill core allowlist and hides advanced dashboard tabs by default.
`full` mode enables all eligible discovered skills and shows the full operator surface.

## Chat

The dashboard includes a `Chat` tab. The default `chat` agent uses these skills:

- `memory-recall`
- `taskflow`
- `documentation`

Hermes-style interactive terminal chat:

```sh
birkin-codex
```

The startup screen shows the Birkin ASCII banner, the memory tagline, selected model,
enabled skill count, and Obsidian vault path before the `you>` prompt.
Type `/` to open the command picker. When readline support is available, slash commands
also complete with Tab. `/skills` repairs missing bundled skill files before showing
the enabled skill list, so a pip-installed workspace does not get stuck with an empty
skill catalog. `/skills health` shows the catalog checks, `/skills all` shows the
full discovered catalog, and `/skill NAME` shows one skill's status, source path, and
body command.
Use `/update --dry-run` to inspect the self-update command from chat, or `/update` to
run it.

Interactive commands:

- `/` shows the command picker.
- `/live` switches to the best available live model profile and turns execution on.
- `/setup` shows readiness checks.
- `/dashboard` shows the local dashboard command and URL.
- `/skills` shows enabled skills.
- `/skills health` shows skill configuration checks.
- `/skills all` shows the full discovered skill catalog.
- `/skills search TEXT` searches skill names and descriptions.
- `/skill NAME` shows one skill's status, source path, and body command.
- `/mode lite` switches back to the small default surface.
- `/mode full` enables all eligible skills and advanced controls.
- `/model ID` switches the model profile for the current chat.
- `/execute on` allows the selected runner to execute.
- `/execute off` returns to packet-only safe mode.
- `/status` shows the active chat model, mode, skill count, execution state, and vault.
- `/update --dry-run` previews the self-update command; `/update` runs it.
- `/exit` leaves chat.

## Update

Update the installed CLI from the configured repository and ref:

```sh
birkin-codex update --dry-run
birkin-codex update
birkin-codex update --method pip --repo https://github.com/ashmoonori-afk/birkin-agent --ref main
```

`update` uses `uv tool install --force`, `pipx install --force`, or
`python -m pip install --upgrade` in that order when `--method auto` is selected.
`BIRKIN_REPO` and `BIRKIN_REF` can override the default source.

Packet-only chat:

```sh
birkin-codex chat --message "Summarize this workspace" --model packet
birkin-codex chat --dry-run --message "Summarize this workspace"
```

Packet mode is the first-run success path. It creates a run record, recalls memory,
captures the conversation, and explains how to switch to live execution without
requiring API keys up front.

Prompt packet debugging:

```sh
birkin-codex agents packet chat --task "Summarize this workspace" --format summary
birkin-codex agents packet chat --task "Summarize this workspace" --format prompt
```

The summary format reports the agent, model, runner, prompt style, sections, routed
skills, recalled memory count, estimated tokens, and prompt size. The prompt format
prints the exact text sent to packet/API/local CLI runners.

Executed chat through a configured model profile:

```sh
birkin-codex chat --message "Draft the next plan" --model codex-local --execute
```

The dashboard chat form uses `/api/chat`. The gateway exposes the same operation at
`POST /api/chat`.

## Skill Config Verification

Run:

```sh
birkin-codex skills config
birkin-codex skills config --json
birkin-codex skills validate
birkin-codex skills safety
birkin-codex skills sync
birkin-codex skills sync --json
```

`skills config` reports:

- Configured skill roots.
- Discovered skill count.
- Enabled and eligible skill count.
- Gated skill count.
- Shadowed duplicate skill files.
- Enabled/disabled selection state.
- Hermes and OpenClaw reflection counts.
- Exact upstream mirror completeness.
- Registry consistency for canonical id, path, source, enabled state, and list/view agreement.
- Skill safety summary for permission metadata, versions, hashes, and immutable upstream mirrors.

`skills sync` is intentionally non-mutating in this repo. Birkin Codex already ships exact
Hermes/OpenClaw mirrors under `skills/upstream`, and those upstream mirrors are immutable.
The command reports mirror health, the hot-reload policy, and the enabled+eligible gating
policy without copying over existing upstream files.

This check is separate from `skills validate`, which still validates each `SKILL.md`
frontmatter and body. `skills validate` also includes the config-level checks.

`skills safety` lists per-skill permission manifest, version, author/source, computed
hash, tests, last verified value, and whether the skill is immutable."""


MEMORY_LEDGER_TELEGRAM_DOC = r"""# Memory, Ledger, and Telegram

Scope date: 2026-05-28.

Birkin stores durable memory as markdown notes in an Obsidian-compatible vault, appends
usage records to a JSONL ledger, and can onboard Telegram bot notifications without
storing bot tokens in the workspace.

## Obsidian Memory

Default vault:

```text
memory/obsidian-vault
```

Commands:

```sh
birkin-codex memory status
birkin-codex memory set-vault /path/to/vault --allow-external
birkin-codex memory record --kind feedback --text "USER_CORRECTION: ..."
birkin-codex memory recall "search phrase"
```

Automatic capture:

- Chat messages and replies are written under `Birkin/Conversations`.
- Run summaries are written under `Birkin/Runs`.
- Failed runs are written under `Birkin/Errors`.
- Manual feedback goes under `Birkin/Feedback`.

Chat calls run memory recall before building the prompt and include matching note
snippets in a `Recalled Memory` section.

## Ledger

Ledger path:

```text
usage/ledger.jsonl
```

Commands:

```sh
birkin-codex ledger summary
birkin-codex ledger list
```

Each entry records run id, agent, status, model, runner, estimated prompt tokens,
provider token fields, and a `costUsd` field. Cost remains `0.0` until pricing rules are
configured. OpenAI-compatible API responses contribute provider token fields when the
response includes a `usage` object.

## Telegram Onboarding

Telegram stores only the chat id and token environment variable name:

```sh
birkin-codex telegram setup --chat-id 123456 --token-env TELEGRAM_BOT_TOKEN --enable
birkin-codex telegram status
birkin-codex telegram test --message "Birkin is connected."
```

Set the token outside the repo:

```sh
export TELEGRAM_BOT_TOKEN=...
```

On Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "..."
```

## Wizard

The first-run wizard configures model selection, Obsidian memory, and Telegram:

```sh
birkin-codex setup wizard
```

Non-interactive example:

```sh
birkin-codex setup wizard \
  --model codex-local \
  --obsidian-vault memory/obsidian-vault \
  --telegram-chat-id 123456 \
  --telegram-token-env TELEGRAM_BOT_TOKEN \
  --enable-telegram \
  --non-interactive
```"""


RUNTIME_APPROVAL_MORPHEUS_DOC = r"""# Runtime, Approvals, and Morpheus

Scope date: 2026-05-28.

Birkin Codex keeps packet, local CLI, and API runners, then adds one structured
OpenAI-compatible `tool-agent` runtime through the `api-agent` model profile.

The tool runtime can load skills, write/search/get/link semantic memory, read/list
workspace files, and spawn packet-only subagents. Consequential actions such as shell,
external web fetch, Telegram send, scheduling, and model-requested file writes are queued
under approvals.

```sh
birkin-codex approvals list
birkin-codex approvals approve <approval-id>
birkin-codex approvals reject <approval-id>
birkin-codex morpheus --dry-run
birkin-codex daemon status
```

Morpheus is the 04:00 self-improvement review. It reads recent conversations, runs,
errors, feedback, ledger rows, and changed files. It applies only high-evidence safe
memory updates; weak evidence and skill changes become verified-learning proposals.
"""


VERIFIED_LEARNING_RELIABILITY_DOC = r"""# Verified Learning and Reliability

Scope date: 2026-05-28.

Birkin is a verified-learning, reliability-first agent OS. Memory, skill, and
self-improvement changes can store evidence, confidence, TTL, scope, author/agent,
reason, blame, and rollback metadata.

Commands:

```sh
birkin-codex learning list
birkin-codex learning events
birkin-codex learning approve <proposal-id>
birkin-codex learning reject <proposal-id>
birkin-codex learning rollback <event-id>
birkin-codex reliability health
birkin-codex reliability traces
birkin-codex reliability budget
```

Morpheus applies only high-evidence safe memory updates. Weak evidence and skill changes
become reviewable proposals.
"""


DEFAULT_DOC_FILES = {
    "docs/reference-notes.md": REFERENCE_NOTES,
    "docs/architecture.md": ARCHITECTURE_DOC,
    "docs/dashboard.md": DEFAULT_DASHBOARD_DOC,
    "docs/macos.md": MACOS_DOC,
    "docs/model-selection.md": MODEL_SELECTION_DOC,
    "docs/auth-api-gateway.md": AUTH_API_GATEWAY_DOC,
    "docs/setup-chat-skills.md": SETUP_CHAT_SKILLS_DOC,
    "docs/memory-ledger-telegram.md": MEMORY_LEDGER_TELEGRAM_DOC,
    "docs/runtime-approval-morpheus.md": RUNTIME_APPROVAL_MORPHEUS_DOC,
    "docs/verified-learning-reliability.md": VERIFIED_LEARNING_RELIABILITY_DOC,
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

Birkin is a verified-learning, reliability-first agent OS inspired by Hermes Agent and
OpenClaw. It is built so the agent does not learn wrong things, does not silently fail,
and acts through approval-first governance.

## Quick Start

One-line install:

```sh
curl -fsSL https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.sh | sh
birkin-codex
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.ps1 | iex
birkin-codex
```

Editable source checkout:

```sh
python -m pip install -e .
birkin-codex
birkin-codex web --port 8765
```

First run starts in safe packet mode and still creates a run record plus memory note.
Use `/live` in chat after connecting a local CLI or API model.

## Core Surfaces

- `birkin-codex`: Hermes-style interactive CLI.
- `birkin-codex setup wizard`: model, Obsidian, and Telegram onboarding.
- `birkin-codex memory`: typed, scoped, versioned Obsidian memory.
- `birkin-codex learning`: evidence-backed proposal review and rollback.
- `birkin-codex approvals`: risk-tiered approval inbox.
- `birkin-codex reliability`: health, traces, delivery log, and budget status.
- `birkin-codex skills safety`: skill permissions, versions, hashes, and immutable mirrors.
- `birkin-codex morpheus --dry-run`: conservative self-improvement review.

See the repository README and docs for the full implementation, tradeoffs, and roadmap.
"""
