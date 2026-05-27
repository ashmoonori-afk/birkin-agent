# macOS Usage

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

Birkin does not call a model by default. To connect a local CLI, edit `birkin.json`:

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

Keep the command as an argv array. Do not put shell pipelines or secrets in this config.
