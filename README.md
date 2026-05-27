# Birkin Agent

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
.\scripts\birkin.ps1 doctor
.\scripts\birkin.ps1 skills list
.\scripts\birkin.ps1 agents run planner --task "Plan the next release"
.\scripts\birkin.ps1 web --port 8765
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
`.\scripts\birkin.ps1` on Windows.

## More

- [Architecture](docs/architecture.md)
- [Dashboard](docs/dashboard.md)
- [macOS usage](docs/macos.md)
- [Reference notes](docs/reference-notes.md)
