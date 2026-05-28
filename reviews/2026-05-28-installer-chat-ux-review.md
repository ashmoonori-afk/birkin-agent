# Code Review: Installer and Chat-First UX

Date: 2026-05-28

## Scope

Reviewed the one-line installer scripts, generated workspace templates, chat-first CLI
copy, `/live` model selection, packet-mode first-run response, README/docs updates, and
tests for the installer and interactive chat changes.

## Findings

No blocking findings remain.

## Notes

- One-line installers mirror the lighter Birkin installer shape: `uv`, then `pipx`, then
  `pip --user`, with `BIRKIN_REPO` and `BIRKIN_REF` overrides for testing alternate
  remotes or branches.
- The no-argument chat entry now explains safe packet mode first and keeps operational
  surfaces behind explicit commands.
- Packet-only chat now returns a useful first-run success message instead of only saying
  that no runner executed.
- `/live` prefers `api-agent` when `OPENAI_API_KEY` is present, then `codex-local` when
  the local `codex` binary exists, then other runnable configured profiles.
- Generated workspaces now include the installer scripts through `DEFAULT_SCRIPT_FILES`.

## Residual Risk

- The installer scripts were syntax-reviewed and documented, but not executed against the
  remote GitHub URL because that would modify the user-level tool installation.
- `/live` detects default OpenAI-compatible API readiness through `OPENAI_API_KEY`; custom
  API profiles with non-default key variables still need manual `birkin-codex model use`
  and `/execute on`.
- The dashboard remains feature-rich by design; this change improves the CLI first-run
  path and documentation rather than redesigning the dashboard navigation.

## Verification

- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests` (30 tests)
- `git diff --check -- . ':!skills/upstream'`
- `py -m birkin_agent chat --message "hello" --model packet --json`
- `py -m birkin_agent doctor`
- `py -m birkin_agent skills validate`
- `py -m birkin_agent skills config --json`
- `py -m birkin_agent skills safety --json`
- `py -m birkin_agent setup --json`
