from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .workspace import Workspace


DEFAULT_TELEGRAM_CONFIG = {
    "enabled": False,
    "botTokenEnv": "TELEGRAM_BOT_TOKEN",
    "chatId": "",
    "parseMode": "",
}


def telegram_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("telegram", {})
    for key, value in DEFAULT_TELEGRAM_CONFIG.items():
        config.setdefault(key, value)
    return config


def configure_telegram(
    workspace: Workspace,
    chat_id: str,
    bot_token_env: str = "TELEGRAM_BOT_TOKEN",
    enabled: bool = True,
    parse_mode: str = "",
) -> None:
    config = telegram_config(workspace)
    config["chatId"] = chat_id
    config["botTokenEnv"] = bot_token_env
    config["enabled"] = bool(enabled)
    config["parseMode"] = parse_mode
    workspace.save_config()


def telegram_status(workspace: Workspace) -> dict[str, Any]:
    config = telegram_config(workspace)
    token_env = str(config.get("botTokenEnv") or "TELEGRAM_BOT_TOKEN")
    return {
        "enabled": bool(config.get("enabled") or False),
        "botTokenEnv": token_env,
        "tokenPresent": bool(os.getenv(token_env)),
        "chatId": str(config.get("chatId") or ""),
        "parseMode": str(config.get("parseMode") or ""),
    }


def validate_telegram(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    status = telegram_status(workspace)
    if not status["enabled"]:
        warnings.append("telegram onboarding is not enabled")
        return errors, warnings
    if not status["chatId"]:
        errors.append("telegram.chatId is required when telegram is enabled")
    if not status["tokenPresent"]:
        errors.append(f"telegram bot token environment variable is not set: {status['botTokenEnv']}")
    return errors, warnings


def send_telegram_message(workspace: Workspace, message: str) -> dict[str, Any]:
    status = telegram_status(workspace)
    if not status["enabled"]:
        raise ValueError("telegram is not enabled")
    token = os.getenv(str(status["botTokenEnv"]) or "")
    if not token:
        raise ValueError(f"telegram bot token environment variable is not set: {status['botTokenEnv']}")
    chat_id = str(status["chatId"] or "")
    if not chat_id:
        raise ValueError("telegram chatId is required")
    payload = {"chat_id": chat_id, "text": message}
    parse_mode = str(status.get("parseMode") or "")
    if parse_mode:
        payload["parse_mode"] = parse_mode
    data = urlencode(payload).encode("utf-8")
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            parsed = json.loads(response.read().decode("utf-8"))
            return {"returncode": 0, "stdout": json.dumps(parsed, ensure_ascii=False), "stderr": ""}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"returncode": 1, "stdout": "", "stderr": f"HTTP {exc.code}: {body[:1000]}"}
    except (URLError, OSError) as exc:
        return {"returncode": 1, "stdout": "", "stderr": f"telegram request failed: {exc}"}
