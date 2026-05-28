# Model Selection

Scope date: 2026-05-28.

Birkin uses model profiles to keep model choice separate from agent roles. The default
profile is `packet`, which never calls an external model.

## Commands

```sh
birkin-codex model list
birkin-codex model use packet
birkin-codex model use codex-local
birkin-codex model use api-openai
birkin-codex agents run builder --model codex-local --execute --task "Implement the change"
```

`birkin-codex models` is an alias for `birkin-codex model`.

## Local CLI Profiles

Profiles live in `birkin.json` under `models.profiles`. A profile can define a local
CLI argv template. The placeholders `{model}`, `{provider}`, and `{profile}` are replaced
at run time.

```json
{
  "models": {
    "default": "packet",
    "profiles": {
      "codex-local": {
        "provider": "openai-codex-cli",
        "model": "gpt-5.5",
        "runner": "local-cli",
        "command": ["codex", "exec", "--model", "{model}", "-"],
        "timeoutSeconds": 1800
      }
    }
  }
}
```

Add a custom profile without editing JSON by hand:

```sh
birkin-codex model add my-local \
  --provider local-cli \
  --model local-model \
  --runner local-cli \
  --command-json '["my-model-cli","--model","{model}","-"]'
```

When a local CLI profile executes, Birkin does not send a bare task string. It builds a
prompt packet containing:

- Birkin identity and safety boundaries.
- Workspace prompt files.
- Obsidian memory digest for the task.
- Compact skill catalog.
- Routed skill bodies, including upstream mirror bodies when applicable.
- The task.

This keeps Codex, Claude, or another configured CLI acting as Birkin while still letting
that CLI use its own login store and internal tool loop.

Inspect the exact packet before running a model:

```sh
birkin-codex agents packet builder --model codex-local --task "Plan a refactor" --format summary
birkin-codex agents packet builder --model codex-local --task "Plan a refactor" --format prompt
```

## API Profiles

API model profiles use the `api` runner and point at an API profile with `apiProfile`:

```json
{
  "models": {
    "profiles": {
      "api-openai": {
        "provider": "openai-compatible",
        "model": "gpt-5.5",
        "runner": "api",
        "apiProfile": "openai-compatible",
        "command": [],
        "timeoutSeconds": 1800
      }
    }
  }
}
```

Add a local OpenAI-compatible endpoint and model profile:

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

## Safety

- Model profiles do not execute unless `birkin-codex agents run --execute` is used.
- Commands are argv arrays, not shell strings.
- Secrets should stay in the local CLI's own auth store or environment, not in `birkin.json`.
- API keys are read from environment variables such as `OPENAI_API_KEY`.
- `birkin-codex chat --dry-run` and `agents packet --format prompt` make zero model
  calls and are the preferred debugging path for prompt packets.
