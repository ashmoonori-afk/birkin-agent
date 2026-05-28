# Memory, Ledger, and Telegram

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
```
