---
name: skill-authoring
description: Author and maintain AgentSkills-compatible SKILL.md folders with safe metadata and verification steps.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["skills", "authoring"], "category": "core"}, "openclaw": {"alwaysInclude": true}}
---

# Skill Authoring

## When to Use

Use this skill when creating, editing, reviewing, or importing a skill.

## Procedure

1. Keep each skill in its own directory with a required `SKILL.md`.
2. Use frontmatter fields `name`, `description`, `version`, `platforms`, and single-line JSON `metadata`.
3. Keep the catalog entry compact. Put detailed procedures in the body and supporting files in `references/`, `templates/`, `scripts/`, or `assets/`.
4. Add `metadata.openclaw.requires` when a skill depends on binaries, environment variables, or config.
5. Include `When to Use`, `Procedure`, `Pitfalls`, and `Verification` sections.
6. Run `birkin skills validate` after changes.

## Pitfalls

- Do not place secrets in skill files.
- Do not use broad destructive commands as examples.
- Do not rely on nested YAML metadata in Birkin. Use single-line JSON metadata.

## Verification

- `birkin skills validate` returns `ok`.
- `birkin skills list` shows the expected source and eligibility.
