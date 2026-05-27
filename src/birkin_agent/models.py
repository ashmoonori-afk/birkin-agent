from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from .workspace import Workspace


@dataclass
class ModelProfile:
    id: str
    provider: str
    model: str
    runner: str
    command: list[str]
    api_profile: str
    timeout_seconds: int | None
    description: str
    is_default: bool = False


def model_config(workspace: Workspace) -> dict[str, Any]:
    return workspace.config.setdefault("models", {"default": "packet", "profiles": {}})


def model_profile_map(workspace: Workspace) -> dict[str, ModelProfile]:
    config = model_config(workspace)
    default_id = str(config.get("default") or "packet")
    raw_profiles = config.get("profiles") or {}
    profiles: dict[str, ModelProfile] = {}
    if isinstance(raw_profiles, list):
        iterable = [(str(raw.get("id") or ""), raw) for raw in raw_profiles if isinstance(raw, dict)]
    elif isinstance(raw_profiles, dict):
        iterable = [(str(key), value) for key, value in raw_profiles.items() if isinstance(value, dict)]
    else:
        iterable = []
    for profile_id, raw in iterable:
        if not profile_id:
            continue
        command = raw.get("command") or []
        if not isinstance(command, list):
            command = []
        timeout = raw.get("timeoutSeconds")
        profiles[profile_id] = ModelProfile(
            id=profile_id,
            provider=str(raw.get("provider") or ""),
            model=str(raw.get("model") or profile_id),
            runner=str(raw.get("runner") or ""),
            command=[str(part) for part in command],
            api_profile=str(raw.get("apiProfile") or ""),
            timeout_seconds=int(timeout) if timeout else None,
            description=str(raw.get("description") or ""),
            is_default=profile_id == default_id,
        )
    return profiles


def list_model_profiles(workspace: Workspace) -> list[ModelProfile]:
    return sorted(model_profile_map(workspace).values(), key=lambda item: item.id)


def default_model_id(workspace: Workspace) -> str:
    config = model_config(workspace)
    return str(config.get("default") or "packet")


def resolve_model_profile(
    workspace: Workspace,
    selector: str | None = None,
    provider: str | None = None,
) -> ModelProfile:
    profiles = model_profile_map(workspace)
    default_id = default_model_id(workspace)
    selected = (selector or default_id).strip()
    if selected in profiles:
        profile = profiles[selected]
    else:
        base = profiles.get(default_id)
        if base is None:
            base = ModelProfile(
                id=selected or "packet",
                provider="packet",
                model=selected or "packet-only",
                runner="dry-run",
                command=[],
                api_profile="",
                timeout_seconds=None,
                description="Packet-only model profile.",
                is_default=True,
            )
        profile = ModelProfile(
            id=selected,
            provider=base.provider,
            model=selected,
            runner=base.runner,
            command=list(base.command),
            api_profile=base.api_profile,
            timeout_seconds=base.timeout_seconds,
            description=f"Ad hoc model override based on {base.id}.",
            is_default=False,
        )
    if provider:
        profile = ModelProfile(
            id=profile.id,
            provider=provider,
            model=profile.model,
            runner=profile.runner,
            command=list(profile.command),
            api_profile=profile.api_profile,
            timeout_seconds=profile.timeout_seconds,
            description=profile.description,
            is_default=profile.is_default,
        )
    return profile


def render_model_command(command: list[str], profile: ModelProfile) -> list[str]:
    replacements = {
        "{model}": profile.model,
        "{provider}": profile.provider,
        "{profile}": profile.id,
    }
    rendered: list[str] = []
    for part in command:
        value = str(part)
        for marker, replacement in replacements.items():
            value = value.replace(marker, replacement)
        rendered.append(value)
    return rendered


def model_rows(workspace: Workspace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile in list_model_profiles(workspace):
        rows.append(
            {
                "id": profile.id,
                "default": "yes" if profile.is_default else "no",
                "provider": profile.provider,
                "model": profile.model,
                "runner": profile.runner,
                "apiProfile": profile.api_profile,
                "command": " ".join(profile.command) if profile.command else "",
                "description": profile.description,
            }
        )
    return rows


def validate_models(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = model_config(workspace)
    profiles = model_profile_map(workspace)
    default_id = str(config.get("default") or "")
    if not profiles:
        errors.append("models.profiles must define at least one model profile")
    if default_id and default_id not in profiles:
        errors.append(f"models.default profile not found: {default_id}")
    runner_config = workspace.config.get("runners", {})
    for profile in profiles.values():
        if not valid_model_id(profile.id):
            errors.append(f"model profile has invalid id: {profile.id}")
        if not profile.model:
            errors.append(f"{profile.id}: missing model")
        if profile.runner and profile.runner not in runner_config:
            errors.append(f"{profile.id}: runner not found: {profile.runner}")
        if profile.runner == "api":
            api_profiles = workspace.config.get("api", {}).get("profiles", {})
            api_profile = profile.api_profile or workspace.config.get("runners", {}).get("api", {}).get("profile")
            if not api_profile:
                errors.append(f"{profile.id}: api model profile requires apiProfile or runners.api.profile")
            elif isinstance(api_profiles, dict) and api_profile not in api_profiles:
                errors.append(f"{profile.id}: api profile not found: {api_profile}")
        if profile.command and not all(isinstance(part, str) and part for part in profile.command):
            errors.append(f"{profile.id}: command must be a non-empty argv string list")
        if profile.is_default and profile.runner == "local-cli" and not profile.command:
            runner = runner_config.get(profile.runner, {})
            if not runner.get("command"):
                warnings.append(f"{profile.id}: local-cli profile has no command and runner local-cli is empty")
    return errors, warnings


def valid_model_id(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.:/-]+", value))


def add_model_profile(
    workspace: Workspace,
    profile_id: str,
    provider: str,
    model: str,
    runner: str,
    command_json: str,
    timeout_seconds: int | None,
    description: str,
    api_profile: str = "",
) -> None:
    if not valid_model_id(profile_id):
        raise ValueError("model profile id may contain letters, numbers, _, -, ., :, and /")
    try:
        command = json.loads(command_json) if command_json else []
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid command JSON: {exc}") from exc
    if not isinstance(command, list) or not all(isinstance(part, str) and part for part in command):
        raise ValueError("command JSON must be a list of non-empty strings")
    config = model_config(workspace)
    profiles = config.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("models.profiles must be an object before CLI edits")
    profiles[profile_id] = {
        "provider": provider,
        "model": model,
        "runner": runner,
        "command": command,
        "apiProfile": api_profile,
        "timeoutSeconds": timeout_seconds,
        "description": description,
    }
    workspace.save_config()


def use_model_profile(workspace: Workspace, profile_id: str) -> None:
    profiles = model_profile_map(workspace)
    if profile_id not in profiles:
        raise KeyError(f"model profile not found: {profile_id}")
    config = model_config(workspace)
    config["default"] = profile_id
    workspace.save_config()
