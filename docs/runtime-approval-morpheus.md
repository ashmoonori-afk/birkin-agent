# Runtime, Approvals, and Morpheus

Scope date: 2026-05-28.

Birkin Codex keeps the original packet, local CLI, and API runners, then adds one
structured tool-calling runtime named `tool-agent`.

## Tool-Calling Runtime

Use the `api-agent` model profile:

```sh
birkin-codex model use api-agent
birkin-codex agents run builder --model api-agent --execute --task "Use tools when useful."
```

The runtime calls OpenAI-compatible chat completions with function tools. The model can:

- `load_skill`
- `memory_write_note`
- `memory_search`
- `memory_get_note`
- `memory_link`
- `read_file`
- `list_files`
- `write_file`
- `run_shell`
- `web_fetch`
- `spawn_subagent`
- `schedule_daily`
- `telegram_send`

Safe memory and skill actions can apply directly. Consequential actions are queued.

## Approval Gate

Consequential actions are stored in `approvals/pending` until reviewed:

```sh
birkin-codex approvals list
birkin-codex approvals approve <approval-id>
birkin-codex approvals reject <approval-id>
```

The dashboard and gateway expose the same review flow:

```text
GET  /api/approvals
POST /api/approvals
```

Approval-gated categories include shell, external web fetch, Telegram send, scheduling,
and model-requested file writes. Approved history is stored under `approvals/history`.

## Morpheus

Morpheus is the 04:00 self-improvement review. It is intentionally conservative:

- Reads recent conversations, runs, errors, feedback, ledger rows, and changed files.
- Writes semantic memory and repeatable skill lessons when safe.
- Proposes schedules or consequential automation through approvals.
- Does not require an API key for dry-run mode.

Commands:

```sh
birkin-codex morpheus --dry-run
birkin-codex daemon status
birkin-codex daemon run --once
```

The dashboard exposes Morpheus under the `Morpheus` tab and the gateway exposes:

```text
POST /api/morpheus
```

Morpheus is the public name used by the CLI, dashboard, gateway, and docs.

## What Was Ported From Claude Birkin

- Small provider loop idea for tool calls.
- Tool registry pattern.
- Obsidian memory tools and wikilinks.
- Approval queue before consequential actions.
- Unattended self-improvement review, renamed Morpheus here.
- Telegram channel concept with environment-only token handling.

## What Stays Different

- Birkin Codex keeps the existing dashboard, ledger, model/auth/API profiles, and
  exact Hermes/OpenClaw upstream mirrors.
- The default runner remains packet-only.
- Local CLI profiles remain command runners and do not expose structured tool calls.
- Morpheus dry-run is deterministic and no-key safe.
- Gateway auth remains local/token based instead of adding a larger service stack.
