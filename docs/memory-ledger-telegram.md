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
birkin-codex memory write-note --title "User Preference" --body "Prefer local CLI first." --type preference --confidence 0.9 --scope project=birkin_codex --reason "user preference"
birkin-codex memory search "local CLI" --type preference --scope birkin_codex --min-confidence 0.8 --source manual
birkin-codex memory get-note "User Preference"
birkin-codex memory link --from-title "User Preference" --to-title "Model Selection"
```

Automatic capture:

- Chat messages and replies are written under `Birkin/Conversations`.
- Run summaries are written under `Birkin/Runs`.
- Failed runs are written under `Birkin/Errors`.
- Manual feedback goes under `Birkin/Feedback`.

Chat calls run memory recall before building the prompt and include matching note
snippets in a `Recalled Memory` section.

Semantic notes include frontmatter fields for `kind`, `type`, `created`, `updated`,
`confidence`, `version`, `scope`, `sources`, `tags`, `evidence`, `ttlDays`, `expires`,
`author`, `agent`, `reason`, and `blame`. Links are written as Obsidian `[[wikilink]]`
relationships.

Supported memory types are User, Project, Environment, Workflow, Ephemeral, Negative,
Conversation, Run, Error, and Feedback. Negative memory includes revalidation metadata
so temporary environment failures can be revisited instead of learned forever.

All writes append a history row to:

```text
memory/history.jsonl
```

Memory writes also emit verified-learning events with rollback metadata when a previous
file body exists.

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
birkin-codex telegram setup --chat-id 123456 --token-env TELEGRAM_BOT_TOKEN --enable --enable-inbound
birkin-codex telegram status
birkin-codex telegram test --message "Birkin is connected."
birkin-codex telegram poll --once
```

Set the token outside the repo:

```sh
export TELEGRAM_BOT_TOKEN=...
```

On Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "..."
```

The `telegram test` command is explicitly user-triggered and sends immediately.
Telegram sends requested by the tool-calling runtime are queued under approvals.
Inbound long-polling is opt-in and stores received text as conversation memory.

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
  --enable-telegram-inbound \
  --non-interactive
```
