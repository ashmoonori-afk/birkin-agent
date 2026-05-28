from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .workspace import Workspace


@dataclass
class ApiProfile:
    id: str
    type: str
    base_url: str
    api_key_env: str
    chat_path: str
    timeout_seconds: int | None
    description: str


def api_config(workspace: Workspace) -> dict[str, Any]:
    return workspace.config.setdefault("api", {"profiles": {}})


def api_profile_map(workspace: Workspace) -> dict[str, ApiProfile]:
    config = api_config(workspace)
    raw_profiles = config.get("profiles") or {}
    if not isinstance(raw_profiles, dict):
        return {}
    profiles: dict[str, ApiProfile] = {}
    for profile_id, raw in raw_profiles.items():
        if not isinstance(raw, dict):
            continue
        timeout = raw.get("timeoutSeconds")
        profiles[str(profile_id)] = ApiProfile(
            id=str(profile_id),
            type=str(raw.get("type") or "openai-compatible"),
            base_url=str(raw.get("baseUrl") or ""),
            api_key_env=str(raw.get("apiKeyEnv") or ""),
            chat_path=str(raw.get("chatPath") or "/chat/completions"),
            timeout_seconds=int(timeout) if timeout else None,
            description=str(raw.get("description") or ""),
        )
    return profiles


def list_api_profiles(workspace: Workspace) -> list[ApiProfile]:
    return sorted(api_profile_map(workspace).values(), key=lambda item: item.id)


def resolve_api_profile(workspace: Workspace, profile_id: str | None) -> ApiProfile:
    profiles = api_profile_map(workspace)
    selected = (profile_id or "openai-compatible").strip()
    if selected not in profiles:
        raise KeyError(f"api profile not found: {selected}")
    return profiles[selected]


def api_rows(workspace: Workspace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile in list_api_profiles(workspace):
        rows.append(
            {
                "id": profile.id,
                "type": profile.type,
                "baseUrl": profile.base_url,
                "apiKeyEnv": profile.api_key_env,
                "keyPresent": "yes" if profile.api_key_env and os.getenv(profile.api_key_env) else "no",
                "chatPath": profile.chat_path,
                "description": profile.description,
            }
        )
    return rows


def validate_api(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = api_config(workspace)
    raw_profiles = config.get("profiles")
    if raw_profiles is None:
        return errors, warnings
    if not isinstance(raw_profiles, dict):
        errors.append("api.profiles must be an object")
        return errors, warnings
    for profile in list_api_profiles(workspace):
        if not valid_api_id(profile.id):
            errors.append(f"api profile has invalid id: {profile.id}")
        if profile.type != "openai-compatible":
            errors.append(f"{profile.id}: unsupported api profile type: {profile.type}")
        if not profile.base_url:
            errors.append(f"{profile.id}: missing baseUrl")
        if not profile.chat_path.startswith("/"):
            errors.append(f"{profile.id}: chatPath must start with /")
        if profile.api_key_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", profile.api_key_env):
            errors.append(f"{profile.id}: invalid apiKeyEnv: {profile.api_key_env}")
        if profile.api_key_env and not os.getenv(profile.api_key_env):
            warnings.append(f"{profile.id}: environment variable not set: {profile.api_key_env}")
    return errors, warnings


def valid_api_id(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.:/-]+", value))


def endpoint_url(profile: ApiProfile) -> str:
    return profile.base_url.rstrip("/") + "/" + profile.chat_path.lstrip("/")


def call_openai_compatible(
    workspace: Workspace,
    profile_id: str,
    prompt: str,
    model: str,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    profile = resolve_api_profile(workspace, profile_id)
    if profile.type != "openai-compatible":
        raise ValueError(f"{profile.id}: unsupported api profile type: {profile.type}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"content-type": "application/json"}
    if profile.api_key_env:
        api_key = os.getenv(profile.api_key_env)
        if not api_key:
            raise ValueError(f"{profile.id}: environment variable not set: {profile.api_key_env}")
        headers["authorization"] = f"Bearer {api_key}"
    request = Request(endpoint_url(profile), data=data, headers=headers, method="POST")
    timeout = int(timeout_seconds or profile.timeout_seconds or 1800)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return {
                "returncode": 0,
                "stdout": extract_chat_content(parsed),
                "stderr": "",
                "apiProfile": profile.id,
                "model": model,
                "usage": parsed.get("usage") if isinstance(parsed.get("usage"), dict) else {},
                "response": parsed,
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"HTTP {exc.code}: {body[:2000]}",
            "apiProfile": profile.id,
            "model": model,
        }
    except URLError as exc:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"API request failed: {exc.reason}",
            "apiProfile": profile.id,
            "model": model,
        }
    except OSError as exc:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"API request failed: {exc}",
            "apiProfile": profile.id,
            "model": model,
        }
    except json.JSONDecodeError as exc:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"API returned invalid JSON: {exc}",
            "apiProfile": profile.id,
            "model": model,
        }


def extract_chat_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            text = first.get("text")
            if isinstance(text, str):
                return text
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text
    return json.dumps(payload, ensure_ascii=False)


def add_api_profile(
    workspace: Workspace,
    profile_id: str,
    profile_type: str,
    base_url: str,
    api_key_env: str,
    chat_path: str,
    timeout_seconds: int | None,
    description: str,
) -> None:
    if not valid_api_id(profile_id):
        raise ValueError("api profile id may contain letters, numbers, _, -, ., :, and /")
    if profile_type != "openai-compatible":
        raise ValueError("only openai-compatible API profiles are supported")
    config = api_config(workspace)
    profiles = config.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("api.profiles must be an object before CLI edits")
    profiles[profile_id] = {
        "type": profile_type,
        "baseUrl": base_url,
        "apiKeyEnv": api_key_env,
        "chatPath": chat_path,
        "timeoutSeconds": timeout_seconds,
        "description": description,
    }
    workspace.save_config()
