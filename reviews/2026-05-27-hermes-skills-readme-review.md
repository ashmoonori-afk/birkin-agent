# Code Review

Date: 2026-05-27
Scope: README banner, Hermes bundled skill reflections, Hermes skill map, documentation sync, and tests.

## Findings

No blocking issues found.

## Checks Performed

- Correctness: `scripts/birkin.ps1 skills list --json` reports 168 skills total, including 90 `hermes-` reflections and 57 `openclaw-` reflections.
- Metadata: every Hermes reflection has `upstreamSkill`, `upstreamPath`, and `upstreamCommit` metadata.
- Source boundary: Hermes reflections are capability markers only; they do not vendor Hermes runtime code or execute upstream scripts.
- Documentation: README top banner and tagline are present, and README now links the Hermes skill reflection map.
- Compatibility: generated Hermes reflection files use one-line JSON metadata so the existing frontmatter parser can validate them on Windows, macOS, and Linux.

## Validation Evidence

- `scripts/birkin.ps1 skills validate`: `ok`.
- `scripts/birkin.ps1 doctor`: `ok`.
- `PYTHONPATH=src py -m unittest discover -s tests`: 8 tests passed.
- `py -m compileall -q src tests`: passed.

## Residual Risk

- Hermes reflection skills prove catalog coverage and routing intent, not feature parity with Hermes Agent bundled tools.
- macOS execution still needs a real Mac smoke test before claiming platform-level parity beyond Python/POSIX portability.
