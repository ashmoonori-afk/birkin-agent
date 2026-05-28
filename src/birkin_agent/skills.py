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
            try:
                frontmatter, _body, issues = parse_frontmatter(skill_file)
            except OSError:
                continue
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
    config_errors, config_warnings = validate_skill_config(workspace)
    errors.extend(config_errors)
    warnings.extend(config_warnings)
    return errors, warnings


def validate_skill_config(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = workspace.config.get("skills", {})
    if not isinstance(config, dict):
        return ["skills config must be an object"], warnings
    roots = config.get("roots")
    if not isinstance(roots, list) or not roots:
        errors.append("skills.roots must be a non-empty list")
        roots = []
    root_names: set[str] = set()
    for root in roots:
        if not isinstance(root, str) or not root.strip():
            errors.append("skills.roots entries must be non-empty strings")
            continue
        if root in root_names:
            warnings.append(f"skills.roots contains duplicate root: {root}")
        root_names.add(root)
        if Path(root).is_absolute():
            errors.append(f"skills.roots must be workspace-relative: {root}")
    enabled = config.get("enabled")
    if enabled is not None and not isinstance(enabled, list):
        errors.append("skills.enabled must be null or a list")
    disabled = config.get("disabled")
    if disabled is not None and not isinstance(disabled, list):
        errors.append("skills.disabled must be a list")
    allow_targets = config.get("allowSymlinkTargets")
    if allow_targets is not None and not isinstance(allow_targets, list):
        errors.append("skills.allowSymlinkTargets must be a list")

    records = discover_skills(workspace)
    names = {record.name for record in records}
    enabled_names = set(enabled or []) if isinstance(enabled, list) else set()
    disabled_names = set(disabled or []) if isinstance(disabled, list) else set()
    for name in sorted(enabled_names - names):
        errors.append(f"skills.enabled references missing skill: {name}")
    for name in sorted(disabled_names - names):
        warnings.append(f"skills.disabled references missing skill: {name}")
    if records and not any(record.enabled and record.eligible for record in records):
        errors.append("no skills are currently enabled and eligible")
    return errors, warnings


def skill_config_rows(workspace: Workspace) -> list[dict[str, str]]:
    config = workspace.config.get("skills", {})
    records = discover_skills(workspace)
    enabled = [record for record in records if record.enabled and record.eligible]
    gated = [record for record in records if record.enabled and not record.eligible]
    shadowed = sum(len(record.shadowed) for record in records)
    hermes = sum(1 for record in records if record.name.startswith("hermes-"))
    openclaw = sum(1 for record in records if record.name.startswith("openclaw-"))
    upstream = upstream_manifest_status(workspace)
    errors, warnings = validate_skill_config(workspace)
    roots = config.get("roots") if isinstance(config, dict) else []
    enabled_config = config.get("enabled") if isinstance(config, dict) else None
    disabled_config = config.get("disabled") if isinstance(config, dict) else []
    rows = [
        {
            "check": "roots",
            "status": "error" if any("skills.roots" in item for item in errors) else "ok",
            "detail": f"{len(roots) if isinstance(roots, list) else 0} configured roots",
        },
        {
            "check": "catalog",
            "status": "ok" if records else "error",
            "detail": f"{len(records)} discovered skills",
        },
        {
            "check": "enabled",
            "status": "ok" if enabled else "error",
            "detail": f"{len(enabled)} enabled and eligible",
        },
        {
            "check": "gated",
            "status": "warning" if gated else "ok",
            "detail": f"{len(gated)} gated skills",
        },
        {
            "check": "precedence",
            "status": "warning" if shadowed else "ok",
            "detail": f"{shadowed} shadowed duplicate skill files",
        },
        {
            "check": "selection",
            "status": "ok",
            "detail": (
                "all skills allowed"
                if enabled_config is None
                else f"{len(enabled_config) if isinstance(enabled_config, list) else 0} allowlisted"
            ),
        },
        {
            "check": "disabled",
            "status": "warning" if disabled_config else "ok",
            "detail": f"{len(disabled_config) if isinstance(disabled_config, list) else 0} disabled names",
        },
        {
            "check": "reflections",
            "status": "ok" if hermes >= 90 and openclaw >= 57 else "warning",
            "detail": f"{hermes} Hermes, {openclaw} OpenClaw",
        },
        {
            "check": "upstream-mirror",
            "status": "ok" if upstream["total"] >= hermes + openclaw and upstream["missing"] == 0 else "warning",
            "detail": f"{upstream['total']} mirrored upstream skills, {upstream['missing']} missing directories",
        },
    ]
    if errors:
        rows.append({"check": "config-errors", "status": "error", "detail": "; ".join(errors[:3])})
    if warnings:
        rows.append({"check": "config-warnings", "status": "warning", "detail": "; ".join(warnings[:3])})
    return rows


def upstream_manifest_status(workspace: Workspace) -> dict[str, int]:
    manifest = workspace.rel("skills", "upstream", "manifest.json")
    if not manifest.exists():
        return {"total": 0, "missing": 0}
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"total": 0, "missing": 0}
    skills = payload.get("skills") if isinstance(payload.get("skills"), list) else []
    missing = 0
    for row in skills:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or "")
        path = str(row.get("path") or "")
        if not source or not path:
            missing += 1
            continue
        rel = Path(path)
        parts = rel.parts[1:] if rel.parts and rel.parts[0] == "skills" else rel.parts
        if not workspace.rel("skills", "upstream", source, *parts).exists():
            missing += 1
    return {"total": len(skills), "missing": missing}


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
