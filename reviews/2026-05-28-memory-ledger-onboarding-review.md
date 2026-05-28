# Code Review: Memory, Ledger, Wizard, Telegram, and Upstream Skills

Date: 2026-05-28

## Scope

Reviewed the implementation of:

- Obsidian-compatible memory capture and recall in `src/birkin_agent/memory.py`.
- Chat memory injection and chat/run memory capture.
- Usage ledger append, summary, and dashboard/API exposure in `src/birkin_agent/ledger.py`.
- Setup wizard model, memory, and Telegram onboarding in `src/birkin_agent/wizard.py`.
- Telegram status/config/test-send flow in `src/birkin_agent/telegram.py`.
- Exact Hermes/OpenClaw upstream skill mirrors under `skills/upstream/`.
- CLI, gateway, dashboard, docs, defaults, and tests for the new surfaces.

## Findings

No blocking findings remain.

## Changes Made During Review

- Kept exact upstream skill directories in `skills/upstream/` instead of inlining large upstream bodies into reflection files, which keeps dashboard and validation responsive.
- Changed upstream skill body loading to resolve mirror paths from the workspace root instead of assuming the skill root is always `skills/`.
- Kept Obsidian memory writes inside the workspace by default; external vault writes require explicit `--allow-external`.
- Kept Telegram secrets out of `birkin.json`; the config stores only `botTokenEnv` and `chatId`.

## Residual Risk

- Telegram test-send requires a real `TELEGRAM_BOT_TOKEN` and chat id; local validation only verifies config/env presence.
- Ledger cost is `0.0` until provider pricing rules are added.
- Obsidian recall is simple markdown text matching, not vector retrieval.
- Upstream skill mirrors preserve exact skill files, but each skill still depends on its described local tools, accounts, and platform assumptions.

## Verification

```sh
python -m unittest discover -s tests
python -m compileall -q src tests tools
python -m pip install -e .
birkin-codex doctor
birkin-codex setup --json
birkin-codex skills validate
birkin-codex skills config --json
birkin-codex memory status --json
birkin-codex ledger summary --json
birkin-codex telegram status --json
birkin-codex setup wizard --model packet --obsidian-vault memory/obsidian-vault --non-interactive
```

Latest local test run: 18 unit tests passed.

Dashboard smoke:

- `GET http://127.0.0.1:8766/api/status` returned setup status, Obsidian memory status, ledger totals, and Telegram status.
- Served HTML contained Chat, Setup, Memory, Ledger, and Telegram tabs.
- `GET http://127.0.0.1:8770/health` returned `ok`.
- `GET http://127.0.0.1:8770/api/ledger` returned ledger summary.
