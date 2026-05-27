# Code Review

Date: 2026-05-27
Scope: Hermes-style model profiles, local CLI command templates, CLI model commands, dashboard model selector, docs, and tests.

## Findings

No blocking issues found.

## Checks Performed

- Correctness: `birkin model list --json` reports 3 profiles with `packet` as the default.
- Execution path: unit tests cover packet-only selection, Codex CLI command template rendering, and a real local CLI subprocess run through a temporary Python command.
- Safety: model profiles do not execute unless `agents run --execute` is used; commands remain argv arrays, not shell strings.
- Dashboard: model count, model tab, job model column, and job creation model selector render on desktop and mobile with no console errors.
- Compatibility: the default `packet` profile preserves the old dry-run behavior for existing agent commands.

## Validation Evidence

- `PYTHONPATH=src; py -m unittest discover -s tests`: 10 tests passed.
- `py -m compileall -q src tests`: passed.
- `.\scripts\birkin.ps1 doctor`: `ok`.
- `.\scripts\birkin.ps1 skills validate`: `ok`.
- `py -m json.tool birkin.json`: passed.
- `git diff --check`: passed.
- Playwright dashboard smoke: title loaded, 3 model profiles rendered, `codex-local` appears in the Models tab, Run works with `packet`, mobile reload works, no console errors.

## Residual Risk

- `codex-local` requires a working local `codex` CLI login before `--execute` can succeed.
- The `custom-local` profile is a template and must be filled with a real argv command before use.
