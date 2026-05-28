from __future__ import annotations

from typing import Any

from .presets import LITE_SKILLS, experience_mode, is_lite
from .workspace import Workspace


def current_experience(workspace: Workspace) -> dict[str, Any]:
    mode = experience_mode(workspace.config)
    skill_config = workspace.config.get("skills", {})
    enabled = skill_config.get("enabled") if isinstance(skill_config, dict) else None
    return {
        "mode": mode,
        "skills": "lite allowlist" if isinstance(enabled, list) else "all skills",
        "enabledCount": len(enabled) if isinstance(enabled, list) else None,
        "advancedHidden": mode == "lite",
    }


def set_experience_mode(workspace: Workspace, mode: str) -> dict[str, Any]:
    selected = mode.strip().lower()
    if selected not in {"lite", "full"}:
        raise ValueError("mode must be lite or full")
    workspace.config.setdefault("experience", {})["mode"] = selected
    skills = workspace.config.setdefault("skills", {})
    if selected == "lite":
        skills["enabled"] = list(LITE_SKILLS)
    else:
        skills["enabled"] = None
    workspace.save_config()
    return current_experience(workspace)


def is_optional_lite_warning(config: dict[str, Any], source: str, message: str) -> bool:
    if not is_lite(config):
        return False
    if source == "api" and "environment variable not set" in message:
        return True
    if source == "telegram" and message == "telegram onboarding is not enabled":
        return True
    return False
