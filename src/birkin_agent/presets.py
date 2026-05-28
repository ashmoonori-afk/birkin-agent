from __future__ import annotations

from typing import Any


LITE_SKILLS = [
    "memory-recall",
    "taskflow",
    "documentation",
    "code-review",
    "filesystem",
    "shell-runtime",
    "skill-authoring",
    "skill-security-audit",
    "data-analysis",
    "web-research",
    "browser-automation",
    "scheduling",
    "messaging-gateway",
    "subagent-orchestration",
    "self-improvement",
]

EXPERIENCE_MODES = {"lite", "full"}


def experience_config(config: dict[str, Any]) -> dict[str, Any]:
    experience = config.setdefault("experience", {})
    if not isinstance(experience, dict):
        experience = {"mode": "lite"}
        config["experience"] = experience
    mode = str(experience.get("mode") or "lite").strip().lower()
    if mode not in EXPERIENCE_MODES:
        mode = "lite"
    experience["mode"] = mode
    return experience


def experience_mode(config: dict[str, Any]) -> str:
    return str(experience_config(config).get("mode") or "lite")


def is_lite(config: dict[str, Any]) -> bool:
    return experience_mode(config) == "lite"
