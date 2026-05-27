# Code Review: Auth, API, Gateway, and `birkin-codex`

Date: 2026-05-27

## Scope

Reviewed the implementation of:

- Local CLI auth profiles in `src/birkin_agent/auth.py`.
- OpenAI-compatible API execution in `src/birkin_agent/api.py`.
- Local HTTP gateway in `src/birkin_agent/gateway.py`.
- CLI wiring in `src/birkin_agent/cli.py`.
- Model profile integration in `src/birkin_agent/models.py` and `src/birkin_agent/agents.py`.
- Dashboard integration in `src/birkin_agent/dashboard.py` and `src/birkin_agent/web.py`.
- `birkin-codex` entrypoints, tests, and docs.

## Findings

No blocking findings remain.

## Changes Made During Review

- Added an `OSError` catch in `call_openai_compatible` so socket-level API failures return a failed run result instead of escaping unexpectedly.
- Confirmed gateway token handling keeps localhost open by default and requires a bearer token or `x-birkin-token` when `BIRKIN_GATEWAY_TOKEN` is present or `gateway.requireToken` is true.
- Confirmed local CLI auth commands are argv arrays and do not store OAuth tokens in Birkin config.

## Residual Risk

- `birkin auth login codex-cli` still depends on the local `codex login` behavior and any browser or terminal flow it launches.
- `api-openai` requires `OPENAI_API_KEY`; `birkin-codex doctor` reports this as a warning when the variable is not set.
- Gateway login routes run auth commands non-interactively from HTTP requests, so interactive OAuth flows should be started from the CLI when a terminal is required.

## Verification To Run

```sh
python -m unittest discover -s tests
python -m compileall -q src tests
birkin-codex doctor
birkin-codex skills validate
birkin-codex auth list --json
birkin-codex api list --json
birkin-codex gateway routes
```
