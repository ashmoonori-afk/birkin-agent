# Full Structure and Agent Code Review

Date: 2026-05-28

## Scope

- Reviewed the repository structure, packaging, Python agent runtime, chat path,
  skill loader, approvals, memory, Web UI, and gateway code.
- Excluded a line-by-line audit of vendored upstream skill bodies. The review checked
  how those files are packaged, discovered, and exposed.

## Structure Map

- `src/birkin_agent/`: Python package and runtime.
- `skills/`: first-party skills, Hermes/OpenClaw reflection skills, and upstream mirror.
- `docs/`: durable product and architecture docs.
- `scripts/`: Windows and macOS/Linux installer/setup/launcher wrappers.
- `tests/test_birkin.py`: single broad unittest suite covering init, skills, models,
  memory, learning, approvals, gateway, dashboard, and chat.
- `runs/`, `usage/`, `memory/`, `learning/`, `reliability/`, `approvals/`: ignored
  local runtime state.

## Findings

### 1. Web UI execution endpoints are not protected when the server is bound off localhost

Severity: High

`birkin-codex web` accepts `--host`, but `/api/run` and `/api/chat` do not call
`require_local_request`. Only approvals, learning, and Morpheus POST handlers do. If the
server is started with a non-local host, a network peer can create run records and invoke
agent execution through `/api/run` or `/api/chat`. If the request includes
`execute: true` and a live model profile is configured, this can trigger local CLI/API
work.

Evidence:

- `src/birkin_agent/cli.py:213-216` exposes `web --host`.
- `src/birkin_agent/web.py:805-856` handles `/api/run` and `/api/chat` without local
  request or token checks.
- `src/birkin_agent/web.py:858-897` shows the local-request check is only applied to
  approvals, learning, and Morpheus.

Recommendation:

- Apply local-only checks to all POST endpoints by default, or add token auth for the
  Web UI when `--host` is not localhost.
- Add a test that `web --host 0.0.0.0` cannot expose `/api/run` or `/api/chat` without
  explicit auth.

### 2. Gateway `--host` override can expose unauthenticated run/chat APIs

Severity: High

The gateway has token support, but `requireToken` defaults to false. `validate_gateway`
warns only when the configured host is non-localhost. `gateway run --host` overrides the
bind host after validation, so `gateway run --host 0.0.0.0` can bind publicly without
token auth or warning when no token environment variable is set.

Evidence:

- `src/birkin_agent/defaults.py:180-185` sets `gateway.requireToken` to false.
- `src/birkin_agent/cli.py:342-345` exposes `gateway run --host`.
- `src/birkin_agent/gateway.py:68-73` only requires auth when configured or a token is
  present.
- `src/birkin_agent/gateway.py:90-107` validates the configured host, not the runtime
  override.
- `src/birkin_agent/gateway.py:357-371` applies the runtime override after validation.

Recommendation:

- Validate the effective bind host and fail closed unless token auth is enabled for
  non-local binds.
- Consider making gateway token auth required for any host outside localhost.

### 3. Tool-agent turn limit is recorded as success

Severity: Medium

When the tool-agent hits its configured turn limit, `run_tool_agent` returns
`returncode: 0` while putting `tool turn limit reached` in stderr. `run_agent` then maps
that run to status `ok`, which makes dashboards, ledgers, and learning signals treat an
incomplete agent run as successful.

Evidence:

- `src/birkin_agent/runtime.py:141-150` returns `returncode: 0` on tool turn limit.
- `src/birkin_agent/agents.py:396-397` maps `returncode == 0` to status `ok`.
- Reproduced with a fake OpenAI-compatible server that always returns a tool call:
  the saved run status was `ok`, returncode was `0`, and stderr was
  `tool turn limit reached`.

Recommendation:

- Return a non-zero code or a dedicated status such as `incomplete` for turn-limit exits.
- Add a unit test that a repeated tool-call loop is not recorded as `ok`.

### 4. Pip wheel does not include upstream skill support assets

Severity: Medium

The repository contains upstream skill support files such as `scripts/`, `references/`,
`templates/`, and `workflows/`, but package data only includes `SKILL.md` files and the
manifest. A pip-installed workspace can report upstream mirrors as healthy while missing
the supporting scripts that several Hermes/OpenClaw skills reference.

Evidence:

- `pyproject.toml:19-24` packages only `bundled_skills/**/SKILL.md` and
  `bundled_skills/upstream/manifest.json`.
- `src/birkin_agent/skills.py:244-269` copies package resources into new workspaces.
- `src/birkin_agent/skills.py:543-545` reports mirror health by directory count.
- `src/birkin_agent/skills.py:569-590` checks only that mirrored upstream directories
  exist.
- Wheel inspection found 315 bundled `SKILL.md` files but 0 bundled
  `scripts/`, `references/`, `templates/`, or `workflows/` entries.

Recommendation:

- Package the full `src/birkin_agent/bundled_skills/**` tree, or explicitly mark the
  mirror as `SKILL.md`-only in docs and health checks.
- Extend `upstream_manifest_status` to validate expected support files for mirrored
  skills.

### 5. Interactive `/model` accepts missing profiles silently

Severity: Low

The interactive chat command `/model PROFILE` stores the provided string without checking
whether a profile exists. If the name is wrong, model resolution falls back to an ad hoc
profile based on the default profile. In the default packet mode this produces a
packet-only run labeled with the nonexistent model, which looks like a selected model but
does not actually configure one.

Evidence:

- `src/birkin_agent/cli.py:1737-1740` accepts and prints any `/model` value.
- `src/birkin_agent/models.py:75-103` creates an ad hoc fallback profile when a selector
  is not found.
- Reproduced with `/model does-not-exist`; the next chat run reported
  `Current model profile: does-not-exist (dry-run)`.

Recommendation:

- Make `/model PROFILE` validate against `model_profile_map`, or print an explicit
  "ad hoc model override" message with the inherited runner.

## Verification Run

- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests`
- `birkin-codex doctor`
- `birkin-codex doctor --advanced`
- `birkin-codex setup --json`
- `birkin-codex skills validate`
- `birkin-codex skills config`
- `birkin-codex agents packet chat --task "Review smoke" --format summary`
- `birkin-codex update --dry-run --method pip --json`
- `py -m pip wheel . --no-deps --wheel-dir runs\review-wheel`
- Wheel content inspection with `tar -tf` and `rg`

## Review Result

The core packet-safe path and test suite are green. The biggest product risks are not
syntax failures; they are exposure boundaries and false-health/false-success reporting:
non-local Web UI/gateway binds, tool-agent turn-limit success, and pip package mirror
checks that do not include support assets.
