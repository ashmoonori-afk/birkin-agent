# Update Command Review

Date: 2026-05-28

## Findings

No blocking issues found.

## Review Notes

- Added `birkin-codex update` with `--dry-run`, `--json`, `--repo`, `--ref`, and
  `--method auto|uv|pipx|pip`.
- The update path uses argv arrays only. It does not invoke shell pipelines.
- `--method auto` follows the installer order: `uv tool install --force`, then
  `pipx install --force`, then `python -m pip install --upgrade`.
- Interactive chat now supports `/update --dry-run` and `/update`.
- Tests cover the dry-run CLI payload and the interactive slash command path without
  making a network call.

## Residual Risk

- Running `/update` updates the installed package while the current process keeps using
  the already-loaded code. Users should restart the terminal command after a successful
  update.
- `uv`/`pipx`/`pip` availability and permissions are delegated to the local machine.
  Failed package-manager output is surfaced in the command payload.

## Verification

- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests`
- `birkin-codex update --dry-run --method pip --json`
- `birkin-codex doctor`
- `birkin-codex skills validate`
- `git diff --check -- . ':!skills/upstream'`
