# Lite CLI Packet Review

Date: 2026-05-28

## Findings

No blocking issues found.

## Review Notes

- Local CLI execution now receives Birkin identity, prompt files, Obsidian memory digest,
  compact skill catalog, and routed skill bodies through the packet prompt instead of a
  bare task string.
- Packet debugging is explicit through `birkin-codex agents packet --format summary`,
  `birkin-codex agents packet --format prompt`, and `birkin-codex chat --dry-run`.
- Runtime dependency validation checks that the lite core keeps `project.dependencies`
  empty in `pyproject.toml`.
- `skills sync` is correctly non-mutating for the repo-managed Hermes/OpenClaw exact
  mirrors and reports hot-reload plus enabled/eligible selection semantics.
- Dashboard lite mode keeps execute controls hidden until `Show Advanced`, preserving a
  packet-safe first screen.

## Residual Risk

- `skills sync` is intentionally status-only. If a future workflow needs to fetch or
  refresh upstream mirrors, it should be a separate explicit command with attribution,
  diff, and immutability checks.
- Runtime dependency validation currently enforces project package dependencies only. If
  optional extras are added later, they should stay outside the lite default path and be
  checked separately.

## Verification

- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests`
- `birkin-codex doctor`
- `birkin-codex setup --json`
- `birkin-codex mode status`
- `birkin-codex skills validate`
- `birkin-codex skills sync --json`
- `birkin-codex agents packet builder --model codex-local --task "Plan a refactor" --format summary`
- `birkin-codex agents packet builder --model codex-local --task "Plan a refactor" --format prompt`
- `git diff --check -- . ':!skills/upstream'`
- Headless Edge dashboard smoke on `127.0.0.1:8786`: lite hides advanced nav and execute
  controls, `Show Advanced` reveals both, and the `Try Safe Packet` form renders.
