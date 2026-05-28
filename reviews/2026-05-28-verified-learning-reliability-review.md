# Code Review: Verified Learning and Reliability

Date: 2026-05-28

## Scope

Reviewed the verified-learning, Memory OS, approval risk, reliability control-plane,
skill safety, Morpheus, dashboard, gateway, CLI, docs, and tests added in this change.

## Findings

No blocking findings remain.

## Notes

- Morpheus signal collection originally risked recursive self-amplification by reading
  prior `_morpheus.json` records as improvement signals. That was corrected by excluding
  Morpheus/nightly run records from reusable signal collection.
- Dashboard status was initially too slow because skill discovery and safety metadata
  were recomputed repeatedly. Skill discovery now uses a workspace-local cache keyed by
  skill file path, mtime, size, enabled, and disabled state.
- Verified-learning event IDs now include the action to avoid same-second collisions
  between proposal and applied events for the same target.
- Tool-agent memory writes now queue a verified-learning proposal instead of overwriting
  an existing memory note unless an expected version is supplied or append mode is used.
- Dashboard and gateway learning APIs expose show and rollback actions in addition to
  list, approve, and reject.
- Tool-agent skill creation now queues a learning proposal instead of writing `SKILL.md`
  directly.
- Reliability data now exposes replay records derived from delivery events.

## Residual Risk

- Skill permission manifests are now surfaced and enforced as metadata, but most mirrored
  upstream reflection skills still use conservative default permission values until a
  deeper per-skill permission audit is performed.
- Budget governance reports token limits and warnings; provider-specific price tables
  are still roadmap work.
- Always-on production supervision remains roadmap work beyond the local daemon/gateway
  smoke tests.

## Verification

- `py -m pip install -e .`
- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests` (29 tests)
- `git diff --check -- . ':!skills/upstream'`
- `birkin-codex doctor`
- `birkin-codex skills validate`
- `birkin-codex skills config --json`
- `birkin-codex skills safety --json`
- `birkin-codex morpheus --dry-run --json`
- `birkin-codex learning list --json`
- `birkin-codex learning events --json`
- `birkin-codex reliability health --json`
- `birkin-codex reliability budget --json`
- `birkin-codex gateway status --json`
- Dashboard smoke on `127.0.0.1:8768`
- Gateway smoke on `127.0.0.1:8772`
