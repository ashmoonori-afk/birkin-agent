from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import platform
import shutil
from typing import Any

from .util import is_relative_to, slugify
from .workspace import Workspace


@dataclass
class SkillRecord:
    name: str
    description: str
    path: Path
    root: Path
    source: str
    enabled: bool
    eligible: bool
    reason: str = ""
    frontmatter: dict[str, Any] = field(default_factory=dict)
    shadowed: list[Path] = field(default_factory=list)

    @property
    def location(self) -> str:
        return str(self.path.parent)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value == "null":
        return None
    if value.startswith("{") or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            if value.startswith("[") and value.endswith("]"):
                return [part.strip().strip("'\"") for part in value[1:-1].split(",") if part.strip()]
            return value
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str, list[str]]:
    text = path.read_text(encoding="utf-8")
    text = text.lstrip("\ufeff")
    issues: list[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["missing frontmatter"]
    lines = text.splitlines()
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, text, ["unterminated frontmatter"]
    frontmatter: dict[str, Any] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith(" ") or raw.startswith("\t"):
            issues.append("nested YAML is not parsed; use single-line JSON metadata")
            continue
        if ":" not in raw:
            issues.append(f"invalid frontmatter line: {raw}")
            continue
        key, value = raw.split(":", 1)
        frontmatter[key.strip()] = parse_scalar(value)
    body = "\n".join(lines[end + 1 :]) + "\n"
    return frontmatter, body, issues


def metadata_block(frontmatter: dict[str, Any], key: str) -> dict[str, Any]:
    metadata = frontmatter.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get(key)
        return value if isinstance(value, dict) else {}
    return {}


def platform_name() -> str:
    name = platform.system().lower()
    if name == "darwin":
        return "macos"
    if name.startswith("win"):
        return "windows"
    return name


def check_eligibility(frontmatter: dict[str, Any], config: dict[str, Any]) -> tuple[bool, str]:
    current_platform = platform_name()
    platforms = frontmatter.get("platforms")
    if isinstance(platforms, str):
        platforms = [platforms]
    if platforms and current_platform not in platforms:
        return False, f"platform {current_platform} not in {platforms}"

    openclaw = metadata_block(frontmatter, "openclaw")
    if openclaw.get("alwaysInclude") is True:
        return True, ""
    requires = openclaw.get("requires", {})
    if isinstance(requires, dict):
        for binary in requires.get("bins", []) or []:
            if shutil.which(str(binary)) is None:
                return False, f"missing binary: {binary}"
        for env_name in requires.get("env", []) or []:
            if not os.environ.get(str(env_name)):
                return False, f"missing env: {env_name}"
        for key in requires.get("config", []) or []:
            cursor: Any = config
            for part in str(key).split("."):
                if isinstance(cursor, dict) and part in cursor:
                    cursor = cursor[part]
                else:
                    cursor = None
                    break
            if not cursor:
                return False, f"missing config: {key}"
    return True, ""


def iter_skill_files(workspace: Workspace, root: Path) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if child.name.startswith((".", "_")):
            continue
        direct = child / "SKILL.md"
        if direct.exists():
            files.append(direct)
            continue
        if child.is_dir():
            for nested in sorted(child.iterdir(), key=lambda item: item.name):
                if nested.name.startswith((".", "_")):
                    continue
                nested_skill = nested / "SKILL.md"
                if nested_skill.exists():
                    files.append(nested_skill)
    return files


def discover_skills(workspace: Workspace) -> list[SkillRecord]:
    config = workspace.config
    skill_config = config.get("skills", {})
    disabled = set(skill_config.get("disabled") or [])
    enabled = skill_config.get("enabled")
    enabled_set = set(enabled or []) if isinstance(enabled, list) else None
    records_by_name: dict[str, SkillRecord] = {}

    for source in skill_config.get("roots", []):
        root = workspace.rel(source)
        for skill_file in iter_skill_files(workspace, root):
            resolved = skill_file.resolve()
            if not is_relative_to(resolved, root.resolve()):
                continue
            frontmatter, _body, issues = parse_frontmatter(skill_file)
            name = str(frontmatter.get("name") or skill_file.parent.name)
            description = str(frontmatter.get("description") or "")
            eligible, reason = check_eligibility(frontmatter, config)
            enabled_by_config = name not in disabled and (
                enabled_set is None or name in enabled_set
            )
            if issues and not reason:
                reason = "; ".join(issues)
            record = SkillRecord(
                name=name,
                description=description,
                path=skill_file,
                root=root,
                source=source,
                enabled=enabled_by_config,
                eligible=eligible,
                reason=reason,
                frontmatter=frontmatter,
            )
            existing = records_by_name.get(name)
            if existing:
                existing.shadowed.append(skill_file)
            else:
                records_by_name[name] = record
    return list(records_by_name.values())


def validate_skills(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    names: set[str] = set()
    for record in discover_skills(workspace):
        frontmatter, body, issues = parse_frontmatter(record.path)
        for issue in issues:
            errors.append(f"{record.path}: {issue}")
        if not frontmatter.get("name"):
            errors.append(f"{record.path}: missing name")
        if not frontmatter.get("description"):
            errors.append(f"{record.path}: missing description")
        if not body.strip():
            errors.append(f"{record.path}: empty body")
        if record.name in names:
            warnings.append(f"duplicate skill name after precedence: {record.name}")
        names.add(record.name)
        for shadowed in record.shadowed:
            warnings.append(f"{record.name} shadows {shadowed}")
    return errors, warnings


def create_skill(workspace: Workspace, name: str, description: str, group: str = "custom") -> Path:
    slug = slugify(name)
    path = workspace.rel("skills", slugify(group), slug, "SKILL.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    description_value = json.dumps(description)
    content = f"""---
name: {slug}
description: {description_value}
version: 0.1.0
metadata: {{"hermes": {{"tags": ["custom"]}}, "openclaw": {{"alwaysInclude": true}}}}
---

# {name}

## When to Use

Use this skill when the task clearly matches: {description}

## Procedure

1. Confirm the input and required output.
2. Select the smallest safe tool path.
3. Execute inside the workspace boundary.
4. Record reusable lessons with `birkin improve record`.

## Verification

- The output is present in the workspace.
- Claims are backed by files, run records, or cited sources.
"""
    path.write_text(content, encoding="utf-8")
    return path


def skill_rows(workspace: Workspace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in sorted(discover_skills(workspace), key=lambda item: item.name):
        rows.append(
            {
                "name": record.name,
                "enabled": "yes" if record.enabled and record.eligible else "no",
                "source": record.source,
                "description": record.description,
                "reason": record.reason,
            }
        )
    return rows
