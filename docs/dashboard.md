# Dashboard

Scope date: 2026-05-28.

The Birkin Web UI is an operator dashboard, not a landing page. It is served by the
Python standard library:

```sh
birkin-codex web --port 8765
```

Open `http://127.0.0.1:8765`.

## First Screen

- Workspace summary.
- Estimated usage from job prompt packets.
- Running jobs.
- Completed and failed job counts.
- Recent job results with status, agent, model, task, result summary, usage, and timestamp.
- Model profile count and a model selector for new jobs.
- Auth, API, and gateway tabs for integration status.
- Memory, ledger, and Telegram tabs for onboarding and durable status.
- Approval, Morpheus, daemon, and schedule status.
- Setup and skill config tabs for readiness verification.
- Chat tab for message-oriented agent runs.
- Warnings in a separate panel.
- A job creation form that writes a dry-run record by default and can explicitly
  execute the selected runner when the execute checkbox is enabled.

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
- `/api/morpheus` for manual Morpheus dry-runs from the dashboard.
- `/api/status` for setup and skill config status shown in the dashboard tabs.
- `memory/`, `reviews/`, and `runs/` for improvement signals.

## Warning Model

Warnings are separate from job results. They include workspace doctor warnings, skill
validation warnings, model profile warnings, auth/API/gateway warnings, pending
approvals, agent allowlist warnings, and gated skills such as missing environment
variables or missing config.
