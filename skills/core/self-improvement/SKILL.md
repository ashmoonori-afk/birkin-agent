---
name: self-improvement
description: Turn run evidence, user corrections, and review findings into pending skill improvement proposals.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["learning", "memory"], "category": "core"}, "openclaw": {"alwaysInclude": true}}
---

# Self Improvement

## When to Use

Use this skill after a complex task, a repeated mistake, a user correction, or a review finding that should change future behavior.

## Procedure

1. Record the reusable lesson with `birkin improve record --lesson "LESSON: ..." --skill <skill-name>`.
2. Generate a pending proposal with `birkin improve propose`.
3. Review the proposal for evidence, scope, and safety.
4. Apply only after approval with `birkin improve apply <proposal> --skill <skill-name> --yes`.
5. Run `birkin skills validate` and a relevant dry-run agent packet.

## Pitfalls

- Do not update skills from weak or one-off evidence.
- Do not overwrite a skill when a small appended patch is enough.
- Do not treat a proposal as applied until the target `SKILL.md` changed.

## Verification

- The proposal cites a source in `runs/`, `reviews/`, or `memory/`.
- The skill patch is visible in the target `SKILL.md`.
