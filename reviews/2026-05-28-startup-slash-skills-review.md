# Startup Slash Skills Review

Date: 2026-05-28

## Findings

No blocking issues found.

## Review Notes

- The no-argument chat startup now shows the Birkin ASCII banner, memory tagline,
  selected model label, enabled skill count, and Obsidian vault path.
- Chat now has a command picker: `/`, `/help`, and `/commands` show available commands,
  and readline-backed shells get slash command Tab completion when available.
- `/status` reports active agent, model, mode, enabled skill count, execution state, and
  vault path.
- Skill commands, setup, dashboard data, and agent packet building now repair missing
  bundled skill files before discovery.
- The pip wheel includes `birkin_agent/bundled_skills`, so a pip/uv-installed workspace
  can bootstrap the skill catalog without depending on the repo checkout.
- `.gitattributes` disables whitespace checks only for bundled upstream mirror copies so
  the package can preserve upstream `SKILL.md` bodies without failing repo diff checks.

## Residual Risk

- Windows terminals do not always expose stdlib `readline`; those users still get the
  `/` command picker, but not native Tab completion.
- Bundled skill repair is non-overwriting. If a user has a corrupt existing `SKILL.md`,
  validation will still report it instead of replacing user-owned content.

## Verification

- `py -m compileall -q src tests tools`
- `py -m unittest discover -s tests`
- `birkin-codex doctor`
- `birkin-codex skills config`
- `birkin-codex skills validate`
- Empty workspace smoke: `birkin-codex init` then `birkin-codex skills config` repaired
  the catalog to 168 discovered skills, 15 enabled, 90 Hermes reflections, 57 OpenClaw
  reflections, and 147 mirrored upstream skills.
- Wheel smoke: `py -m pip wheel . --no-deps` produced a wheel containing 315 bundled
  `SKILL.md` files.
