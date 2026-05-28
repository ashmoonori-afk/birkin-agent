# Dashboard

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
- How close is the workspace to configured per-run, daily, or monthly token budgets?
