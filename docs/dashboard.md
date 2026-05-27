# Dashboard

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
- Recent job results with status, agent, model, task, result summary, usage, and timestamp.
- Model profile count and a model selector for new jobs.
- Warnings in a separate panel.
- A job creation form that writes a dry-run record by default.

## Data Source

The dashboard reads:

- `runs/*.json` for job history, summaries, status, and usage.
- `skills/**/SKILL.md` for skill status and gating warnings.
- `birkin.json` for agents, models, runners, and allowlists.
- `memory/`, `reviews/`, and `runs/` for improvement signals.

## Warning Model

Warnings are separate from job results. They include workspace doctor warnings, skill
validation warnings, model profile warnings, agent allowlist warnings, and gated skills
such as missing environment variables or missing config.
