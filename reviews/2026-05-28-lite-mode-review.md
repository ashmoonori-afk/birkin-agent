# Lite Mode Review

Date: 2026-05-28

## Scope

- Reviewed the lite/full experience switch in `src/birkin_agent/presets.py` and
  `src/birkin_agent/experience.py`.
- Reviewed CLI behavior in `src/birkin_agent/cli.py` for `doctor`, `setup`, chat slash
  commands, and `mode status|use`.
- Reviewed dashboard API and Web UI behavior in `src/birkin_agent/dashboard.py` and
  `src/birkin_agent/web.py`.
- Reviewed default config, workspace config, tests, and docs touched by the change.

## Findings

No blocking issues found.

## Notes

- Lite mode hides only optional integration warnings for missing API keys and disabled
  Telegram onboarding. Config errors and gateway/auth safety warnings remain visible.
- The dashboard still exposes the full data payload through `/api/status`; lite mode is
  a default UX filter, not a security boundary.
- `mode use full` enables all eligible discovered skills by setting `skills.enabled` to
  `null`; gated skills still respect platform, env, and config eligibility checks.

## Verification

- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests`
- `py -m birkin_agent doctor`
- `py -m birkin_agent doctor --advanced`
- `py -m birkin_agent setup --json`
- `py -m birkin_agent setup --advanced --json`
- `py -m birkin_agent mode status --json`
- `py -m birkin_agent skills validate`
- `py -m birkin_agent skills config --json`
- `git diff --check -- . ':!skills/upstream'`
- Headless Edge dashboard smoke: `Birkin Agent`, advanced tabs hidden in lite mode,
  advanced tabs visible after `Show Advanced`, warning count `0`.
