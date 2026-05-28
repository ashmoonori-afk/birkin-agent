# Reference Notes

Scope date: 2026-05-28.

Reference snapshot:

- Hermes Agent commit: `2d5dcfabc312d43f87a4f0f44c45f62cf24a09b2`
- OpenClaw commit: `d00e764e66555320ac75f048c2767ba5877de0a9`

## Sources Used

- Hermes Agent repository: https://github.com/NousResearch/hermes-agent
- Hermes CLI commands documentation: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/cli-commands.md
- Hermes skills documentation: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md
- Hermes bundled skills catalog: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/skills-catalog.md
- OpenClaw repository: https://github.com/openclaw/openclaw
- OpenClaw skills documentation: https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md
- OpenClaw tools overview: https://github.com/openclaw/openclaw/blob/main/docs/tools/index.md

## Design Inputs Reflected

- AgentSkills-compatible `SKILL.md` folders with frontmatter.
- Progressive disclosure: list metadata first; load full bodies only when needed.
- Agent-managed skills through proposal and apply commands.
- Skill precedence with workspace roots before lower-priority roots.
- Skill gating by platform, environment variables, and required binaries.
- Per-agent skill allowlists.
- Model selection through configured provider/model profiles and per-run overrides.
- Obsidian-style note storage for durable memory.
- JSONL usage ledger for run and token accounting.
- Telegram bot onboarding through environment-backed secrets.
- Snapshot-style prompt packets for CLI subagent execution.
- Web UI as an operator control surface, not a separate backend product.
- Self-improvement loop based on run records, reviews, memory notes, and user corrections.
- Hermes bundled skill coverage through 90 lightweight `hermes-<name>` reflection skills.
- OpenClaw skill coverage through 57 lightweight `openclaw-<name>` reflection skills.

## Boundary

This workspace reflects the referenced systems in a lightweight Python implementation.
It does not vendor either upstream project or claim API compatibility with their private
runtime internals. Reflection skills preserve source-linked capability intent, not full
upstream implementations.
