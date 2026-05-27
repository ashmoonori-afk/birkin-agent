# Model Selection

Scope date: 2026-05-27.

Birkin uses model profiles to keep model choice separate from agent roles. The default
profile is `packet`, which never calls an external model.

## Commands

```sh
birkin model list
birkin model use packet
birkin model use codex-local
birkin agents run builder --model codex-local --execute --task "Implement the change"
```

`birkin models` is an alias for `birkin model`.

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
birkin model add my-local \
  --provider local-cli \
  --model local-model \
  --runner local-cli \
  --command-json '["my-model-cli","--model","{model}","-"]'
```

## Safety

- Model profiles do not execute unless `birkin agents run --execute` is used.
- Commands are argv arrays, not shell strings.
- Secrets should stay in the local CLI's own auth store or environment, not in `birkin.json`.
