# Auth, API, and Gateway

Scope date: 2026-05-27.

Birkin supports three Hermes-style integration paths while keeping the default runner
safe and local:

- Local CLI auth profiles delegate OAuth/login state to a tool such as `codex`.
- API profiles call OpenAI-compatible chat completions endpoints.
- The gateway exposes a local HTTP control surface for status, model lists, auth status,
  and run creation.

## Local CLI Auth

Birkin does not store OAuth tokens. The default `codex-cli` auth profile calls the local
Codex CLI login, logout, and status commands:

```sh
birkin-codex auth list
birkin-codex auth status codex-cli
birkin-codex auth login codex-cli
birkin-codex auth logout codex-cli
```

The profile lives in `birkin.json` under `auth.profiles.codex-cli`:

```json
{
  "type": "local-cli-oauth",
  "provider": "openai-codex-cli",
  "binary": "codex",
  "loginCommand": ["codex", "login"],
  "logoutCommand": ["codex", "logout"],
  "statusCommand": ["codex", "doctor"]
}
```

Add another OAuth-capable local CLI profile:

```sh
birkin-codex auth add my-cli \
  --provider local-cli \
  --binary my-cli \
  --login-json '["my-cli","login"]' \
  --logout-json '["my-cli","logout"]' \
  --status-json '["my-cli","status"]'
```

Commands are argv arrays. Do not put shell pipelines, token strings, or secrets in
`birkin.json`.

## API Profiles

API profiles target OpenAI-compatible chat completions APIs. The default
`openai-compatible` profile uses `https://api.openai.com/v1` and reads the key from
`OPENAI_API_KEY`.

```sh
birkin-codex api list
birkin-codex model use api-openai
birkin-codex agents run builder --model api-openai --execute --task "Draft the change"
```

For a local server:

```sh
birkin-codex api add local-dev \
  --base-url http://127.0.0.1:1234/v1 \
  --chat-path /chat/completions

birkin-codex model add local-api \
  --provider local-dev \
  --model local-model \
  --runner api \
  --api-profile local-dev
```

The API runner sends one user message containing the built Birkin prompt packet. It
extracts `choices[0].message.content` when the response uses the standard chat
completions shape.

## Gateway

The gateway is a local machine-facing API. It is separate from the dashboard UI.

```sh
birkin-codex gateway routes
birkin-codex gateway status
birkin-codex gateway run --port 8770
```

Default URL:

```text
http://127.0.0.1:8770
```

Routes:

```text
GET /health
GET /routes
GET /api/status
GET /api/models
GET /api/auth
GET /api/api-profiles
GET /api/gateway
GET /api/setup
GET /api/skills/config
GET /api/memory
GET /api/ledger
GET /api/telegram
POST /api/run
POST /api/chat
POST /api/auth/{profile}/status
POST /api/auth/{profile}/login
POST /api/auth/{profile}/logout
```

Create a packet-only run through the gateway:

```sh
curl -s http://127.0.0.1:8770/api/run \
  -H 'content-type: application/json' \
  -d '{"agent":"planner","model":"packet","task":"Plan the next step"}'
```

Set `"execute": true` to allow the selected runner to execute. The same `--execute`
safety boundary used by the CLI is preserved in the gateway request body.

## Token Gate

By default, the gateway binds to `127.0.0.1` without requiring a token. If
`BIRKIN_GATEWAY_TOKEN` is set, or if `gateway.requireToken` is true, requests must include
one of these headers:

```text
Authorization: Bearer <token>
x-birkin-token: <token>
```

If the gateway is configured for a non-localhost host without token auth, `birkin-codex doctor`
reports a warning.
