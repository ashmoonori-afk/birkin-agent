from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
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


def birkin_metadata(frontmatter: dict[str, Any]) -> dict[str, Any]:
    return metadata_block(frontmatter, "birkin")


def permission_manifest(frontmatter: dict[str, Any]) -> dict[str, Any]:
    permissions = frontmatter.get("permissions")
    if isinstance(permissions, dict):
        return permissions
    birkin = birkin_metadata(frontmatter)
    value = birkin.get("permissions")
    return value if isinstance(value, dict) else {"tools": [], "resources": [], "approval": "review"}


def skill_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return ""


def immutable_skill(workspace: Workspace, path: Path) -> bool:
    try:
        frontmatter, _body, _issues = parse_frontmatter(path)
    except OSError:
        return False
    birkin = birkin_metadata(frontmatter)
    rel = path.relative_to(workspace.root).as_posix() if path.is_relative_to(workspace.root) else path.as_posix()
    if birkin.get("upstreamMirror"):
        return True
    if rel.startswith("skills/upstream/"):
        return True
    if "/hermes-reflections/" in rel or "/openclaw-reflections/" in rel:
        return True
    return bool(birkin.get("immutable") is True or frontmatter.get("source") == "official")


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
    roots = [str(source) for source in skill_config.get("roots", [])]
    files_by_root: list[tuple[str, Path, Path]] = []
    signature: list[tuple[str, str, int, int]] = []
    for source in roots:
        root = workspace.rel(source)
        for skill_file in iter_skill_files(workspace, root):
            try:
                stat = skill_file.stat()
            except OSError:
                continue
            files_by_root.append((source, root, skill_file))
            signature.append((source, str(skill_file.relative_to(workspace.root)), stat.st_mtime_ns, stat.st_size))
    cache_key = (tuple(roots), tuple(signature), tuple(sorted(disabled)), tuple(sorted(enabled_set)) if enabled_set is not None else None)
    cached = getattr(workspace, "_skill_discovery_cache", None)
    if isinstance(cached, dict) and cached.get("key") == cache_key:
        return list(cached.get("records") or [])
    records_by_name: dict[str, SkillRecord] = {}

    for source, root, skill_file in files_by_root:
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
    records = list(records_by_name.values())
    try:
        setattr(workspace, "_skill_discovery_cache", {"key": cache_key, "records": records})
    except Exception:
        pass
    return list(records)


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
    registry_errors, registry_warnings = registry_consistency(workspace, records)
    errors.extend(registry_errors)
    warnings.extend(registry_warnings)
    return errors, warnings


def registry_consistency(workspace: Workspace, records: list[SkillRecord] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    records = records or discover_skills(workspace)
    names = set()
    list_rows = {row["name"]: row for row in skill_rows(workspace)} if records else {}
    for record in records:
        canonical = slugify(record.name)
        if not canonical:
            errors.append(f"{record.path}: empty canonical skill id")
        if record.name in names:
            warnings.append(f"duplicate canonical skill id: {record.name}")
        names.add(record.name)
        if not is_relative_to(record.path.resolve(), workspace.root):
            errors.append(f"{record.name}: skill path escapes workspace")
        row = list_rows.get(record.name)
        if not row:
            errors.append(f"{record.name}: list/view registry mismatch")
        elif row["enabled"] not in {"yes", "no"}:
            errors.append(f"{record.name}: enabled state must be yes/no")
        if not record.source:
            warnings.append(f"{record.name}: missing source root")
    return errors, warnings


def skill_safety_rows(workspace: Workspace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in sorted(discover_skills(workspace), key=lambda item: item.name):
        birkin = birkin_metadata(record.frontmatter)
        permissions = permission_manifest(record.frontmatter)
        tests = birkin.get("tests") if isinstance(birkin.get("tests"), list) else record.frontmatter.get("tests")
        if isinstance(tests, str):
            tests_value = tests
        elif isinstance(tests, list):
            tests_value = ",".join(str(item) for item in tests)
        else:
            tests_value = ""
        rows.append(
            {
                "name": record.name,
                "version": str(record.frontmatter.get("version") or ""),
                "author": str(birkin.get("author") or record.frontmatter.get("author") or ""),
                "source": str(birkin.get("source") or record.source),
                "hash": skill_hash(record.path),
                "permissions": json.dumps(permissions, ensure_ascii=False, sort_keys=True),
                "tests": tests_value,
                "lastVerified": str(birkin.get("lastVerified") or record.frontmatter.get("lastVerified") or ""),
                "immutable": "yes" if immutable_skill(workspace, record.path) else "no",
                "path": str(record.path.relative_to(workspace.root)) if record.path.is_relative_to(workspace.root) else str(record.path),
            }
        )
    return rows


def skill_safety_summary(workspace: Workspace) -> dict[str, int]:
    records = discover_skills(workspace)
    immutable = sum(1 for record in records if immutable_skill(workspace, record.path))
    with_permissions = sum(1 for record in records if bool(permission_manifest(record.frontmatter)))
    with_version = sum(1 for record in records if bool(record.frontmatter.get("version")))
    return {
        "total": len(records),
        "immutable": immutable,
        "withPermissions": with_permissions,
        "withVersion": with_version,
        "withHash": len(records),
    }


def skill_config_rows(workspace: Workspace) -> list[dict[str, str]]:
    config = workspace.config.get("skills", {})
    records = discover_skills(workspace)
    enabled = [record for record in records if record.enabled and record.eligible]
    gated = [record for record in records if record.enabled and not record.eligible]
    shadowed = sum(len(record.shadowed) for record in records)
    hermes = sum(1 for record in records if record.name.startswith("hermes-"))
    openclaw = sum(1 for record in records if record.name.startswith("openclaw-"))
    upstream = upstream_manifest_status(workspace)
    safety = skill_safety_summary(workspace)
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
        {
            "check": "registry-consistency",
            "status": "error" if any("registry" in item or "canonical" in item for item in errors) else "ok",
            "detail": "canonical id/path/source/enabled/list-view checks complete",
        },
        {
            "check": "skill-safety",
            "status": "ok",
            "detail": (
                f"{safety['withHash']}/{safety['total']} hashed, "
                f"{safety['withVersion']}/{safety['total']} versioned, "
                f"{safety['immutable']} immutable upstream/official skills"
            ),
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
    content = render_skill_content(name, description)
    path.write_text(content, encoding="utf-8")
    try:
        from .learning import write_learning_event

        write_learning_event(
            workspace,
            action="skill-create",
            target_type="skill",
            target=slug,
            evidence=[{"type": "manual", "ref": "birkin-codex skills create"}],
            confidence=0.9,
            author="user",
            reason="explicit skill creation",
            metadata={"path": str(path.relative_to(workspace.root)), "hash": skill_hash(path)},
            rollback={"kind": "file-restore", "path": str(path.relative_to(workspace.root)), "before": ""},
        )
    except Exception:
        pass
    return path


def render_skill_content(name: str, description: str) -> str:
    slug = slugify(name)
    description_value = json.dumps(description)
    return f"""---
name: {slug}
description: {description_value}
version: 0.1.0
permissions: {{"tools": [], "resources": ["workspace"], "approval": "review"}}
metadata: {{"birkin": {{"author": "user", "source": "custom", "permissions": {{"tools": [], "resources": ["workspace"], "approval": "review"}}, "tests": ["birkin-codex skills validate"], "lastVerified": "", "immutable": false}}, "hermes": {{"tags": ["custom"]}}, "openclaw": {{"alwaysInclude": true}}}}
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
