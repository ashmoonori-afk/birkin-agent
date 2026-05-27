from __future__ import annotations

from pathlib import Path
import re

from .skills import discover_skills
from .util import safe_path, slugify, utc_stamp
from .workspace import Workspace


def append_lesson(workspace: Workspace, lesson: str, skill: str | None = None) -> Path:
    path = workspace.rel("memory", "lessons.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    target = f" target={skill}" if skill else ""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {utc_stamp()}{target} {lesson.strip()}\n")
    return path


def collect_signals(workspace: Workspace) -> list[str]:
    prefixes = workspace.config.get("improvement", {}).get("signalPrefixes", [])
    signals: list[str] = []
    for source in workspace.config.get("improvement", {}).get("sources", []):
        root = workspace.rel(source)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".jsonl", ".txt"}:
                continue
            if not safe_path(workspace.root, str(path.relative_to(workspace.root))).exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                stripped = line.strip()
                if any(marker in stripped for marker in prefixes):
                    signals.append(f"{path.relative_to(workspace.root)}: {stripped}")
    return signals


def find_skill_path(workspace: Workspace, skill_name: str) -> Path | None:
    for skill in discover_skills(workspace):
        if skill.name == skill_name:
            return skill.path
    return None


def propose_improvement(
    workspace: Workspace,
    lesson: str | None = None,
    skill_name: str | None = None,
) -> Path:
    signals = collect_signals(workspace)
    if lesson:
        signals.append(f"manual: {lesson.strip()}")
    target = skill_name or infer_target_skill(workspace, signals)
    proposal = workspace.rel("improvements", f"{utc_stamp()}_{slugify(target or 'general')}.md")
    signal_text = "\n".join(f"- {signal}" for signal in signals) or "- No reusable signal found."
    patch = build_patch_text(signals)
    proposal.write_text(
        f"""# Skill Improvement Proposal

Date: {utc_stamp()}
Target skill: {target or "new-skill-needed"}
Mode: pending approval

## Evidence

{signal_text}

## Proposed Skill Patch

{patch}

## Apply

Review this proposal, then run:

```powershell
py -m birkin_agent improve apply {proposal.name} --skill {target or "<skill-name>"} --yes
```
""",
        encoding="utf-8",
    )
    return proposal


def infer_target_skill(workspace: Workspace, signals: list[str]) -> str | None:
    names = [skill.name for skill in discover_skills(workspace)]
    blob = "\n".join(signals).lower()
    for name in names:
        if name.lower() in blob:
            return name
    return "self-improvement" if names else None


def build_patch_text(signals: list[str]) -> str:
    if not signals:
        return """### Learned Procedure

1. Record a concrete `LESSON:` or `USER_CORRECTION:` in `memory/lessons.md`.
2. Run `birkin improve propose` again.
3. Apply only after review.
"""
    cleaned = [clean_signal(signal) for signal in signals[-5:]]
    lines = ["### Learned Procedure", ""]
    for index, signal in enumerate(cleaned, start=1):
        lines.append(f"{index}. {signal}")
    lines.extend(
        [
            "",
            "### Verification",
            "",
            "- The next similar run references this procedure.",
            "- A reviewer can trace the change back to the proposal evidence.",
        ]
    )
    return "\n".join(lines)


def clean_signal(signal: str) -> str:
    for marker in ["LESSON:", "USER_CORRECTION:", "FIXME:", "TODO(skill):", "FAILED:"]:
        if marker in signal:
            return signal.split(marker, 1)[1].strip()
    return re.sub(r"^[^:]+:\s*", "", signal).strip()


def apply_improvement(workspace: Workspace, proposal_name: str, skill_name: str, yes: bool = False) -> Path:
    if not yes:
        raise PermissionError("apply requires --yes after reviewing the proposal")
    proposal = workspace.rel("improvements", proposal_name)
    if not proposal.exists():
        raise FileNotFoundError(proposal)
    skill_path = find_skill_path(workspace, skill_name)
    if skill_path is None:
        skill_path = workspace.rel("skills", "custom", slugify(skill_name), "SKILL.md")
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(
            f"""---
name: {slugify(skill_name)}
description: Skill created from an approved self-improvement proposal.
version: 0.1.0
metadata: {{"hermes": {{"tags": ["self-improvement"]}}, "openclaw": {{"alwaysInclude": true}}}}
---

# {skill_name}

""",
            encoding="utf-8",
        )
    text = proposal.read_text(encoding="utf-8")
    marker = "## Proposed Skill Patch"
    if marker not in text:
        raise ValueError("proposal missing Proposed Skill Patch section")
    patch = text.split(marker, 1)[1].split("\n## ", 1)[0].strip()
    current = skill_path.read_text(encoding="utf-8")
    if patch not in current:
        skill_path.write_text(current.rstrip() + "\n\n" + patch + "\n", encoding="utf-8")
    return skill_path
