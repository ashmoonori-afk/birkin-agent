from __future__ import annotations

from dataclasses import dataclass
import json
import re
import shutil
import subprocess
from typing import Any

from .workspace import Workspace


@dataclass
class AuthProfile:
    id: str
    type: str
    provider: str
    binary: str
    login_command: list[str]
    logout_command: list[str]
    status_command: list[str]
    description: str
    required: bool = False


def auth_config(workspace: Workspace) -> dict[str, Any]:
    return workspace.config.setdefault("auth", {"profiles": {}})


def auth_profile_map(workspace: Workspace) -> dict[str, AuthProfile]:
    config = auth_config(workspace)
    raw_profiles = config.get("profiles") or {}
    if not isinstance(raw_profiles, dict):
        return {}
    profiles: dict[str, AuthProfile] = {}
    for profile_id, raw in raw_profiles.items():
        if not isinstance(raw, dict):
            continue
        profiles[str(profile_id)] = AuthProfile(
            id=str(profile_id),
            type=str(raw.get("type") or "local-cli-oauth"),
            provider=str(raw.get("provider") or ""),
            binary=str(raw.get("binary") or ""),
            login_command=string_list(raw.get("loginCommand")),
            logout_command=string_list(raw.get("logoutCommand")),
            status_command=string_list(raw.get("statusCommand")),
            description=str(raw.get("description") or ""),
            required=bool(raw.get("required") or False),
        )
    return profiles


def list_auth_profiles(workspace: Workspace) -> list[AuthProfile]:
    return sorted(auth_profile_map(workspace).values(), key=lambda item: item.id)


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(part) for part in value if isinstance(part, str) and part]


def command_binary(profile: AuthProfile) -> str:
    if profile.binary:
        return profile.binary
    for command in [profile.status_command, profile.login_command, profile.logout_command]:
        if command:
            return command[0]
    return ""


def binary_available(profile: AuthProfile) -> bool:
    binary = command_binary(profile)
    return bool(binary and shutil.which(binary))


def auth_rows(workspace: Workspace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile in list_auth_profiles(workspace):
        rows.append(
            {
                "id": profile.id,
                "type": profile.type,
                "provider": profile.provider,
                "binary": command_binary(profile),
                "available": "yes" if binary_available(profile) else "no",
                "required": "yes" if profile.required else "no",
                "description": profile.description,
            }
        )
    return rows


def run_auth_command(
    workspace: Workspace,
    profile_id: str,
    action: str,
    interactive: bool = False,
) -> dict[str, Any]:
    profiles = auth_profile_map(workspace)
    if profile_id not in profiles:
        raise KeyError(f"auth profile not found: {profile_id}")
    profile = profiles[profile_id]
    commands = {
        "login": profile.login_command,
        "logout": profile.logout_command,
        "status": profile.status_command,
    }
    if action not in commands:
        raise ValueError("auth action must be login, logout, or status")
    command = commands[action]
    if not command:
        raise ValueError(f"{profile_id}: auth {action} command is empty")
    if interactive:
        completed = subprocess.run(command, cwd=workspace.root, check=False)
        return {
            "profile": profile_id,
            "action": action,
            "returncode": completed.returncode,
            "stdout": "",
            "stderr": "",
            "interactive": True,
        }
    completed = subprocess.run(
        command,
        cwd=workspace.root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    return {
        "profile": profile_id,
        "action": action,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "interactive": False,
    }


def validate_auth(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = auth_config(workspace)
    raw_profiles = config.get("profiles")
    if raw_profiles is None:
        return errors, warnings
    if not isinstance(raw_profiles, dict):
        errors.append("auth.profiles must be an object")
        return errors, warnings
    for profile in list_auth_profiles(workspace):
        if not valid_auth_id(profile.id):
            errors.append(f"auth profile has invalid id: {profile.id}")
        if profile.type != "local-cli-oauth":
            errors.append(f"{profile.id}: unsupported auth profile type: {profile.type}")
        for action, command in [
            ("login", profile.login_command),
            ("logout", profile.logout_command),
            ("status", profile.status_command),
        ]:
            if command and not all(isinstance(part, str) and part for part in command):
                errors.append(f"{profile.id}: {action} command must be a non-empty argv string list")
        if profile.required and not binary_available(profile):
            warnings.append(f"{profile.id}: auth binary not found on PATH: {command_binary(profile)}")
    return errors, warnings


def valid_auth_id(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.:/-]+", value))


def parse_command_json(label: str, value: str) -> list[str]:
    try:
        command = json.loads(value) if value else []
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(command, list) or not all(isinstance(part, str) and part for part in command):
        raise ValueError(f"{label} JSON must be a list of non-empty strings")
    return command


def add_auth_profile(
    workspace: Workspace,
    profile_id: str,
    profile_type: str,
    provider: str,
    binary: str,
    login_json: str,
    logout_json: str,
    status_json: str,
    description: str,
    required: bool = False,
) -> None:
    if not valid_auth_id(profile_id):
        raise ValueError("auth profile id may contain letters, numbers, _, -, ., :, and /")
    if profile_type != "local-cli-oauth":
        raise ValueError("only local-cli-oauth auth profiles are supported")
    config = auth_config(workspace)
    profiles = config.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("auth.profiles must be an object before CLI edits")
    profiles[profile_id] = {
        "type": profile_type,
        "provider": provider,
        "binary": binary,
        "loginCommand": parse_command_json("login command", login_json),
        "logoutCommand": parse_command_json("logout command", logout_json),
        "statusCommand": parse_command_json("status command", status_json),
        "description": description,
        "required": required,
    }
    workspace.save_config()
