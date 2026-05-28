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
birkin-codex setup wizard
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

Memory and ledger:

```sh
birkin-codex memory status
birkin-codex ledger summary
```

Telegram onboarding:

```sh
birkin-codex telegram setup --chat-id 123456 --token-env TELEGRAM_BOT_TOKEN --enable
```

Chat through the default packet-only profile:

```sh
birkin-codex
birkin-codex chat --message "Summarize this workspace" --model packet
```

Inside interactive chat, `/live` selects `api-agent` when `OPENAI_API_KEY` is present
or `codex-local` when the local `codex` CLI is available.
