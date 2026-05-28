from __future__ import annotations

import json
import os
import time
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
    "inboundEnabled": False,
    "lastUpdateId": 0,
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
    inbound_enabled: bool | None = None,
) -> None:
    config = telegram_config(workspace)
    config["chatId"] = chat_id
    config["botTokenEnv"] = bot_token_env
    config["enabled"] = bool(enabled)
    config["parseMode"] = parse_mode
    if inbound_enabled is not None:
        config["inboundEnabled"] = bool(inbound_enabled)
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
        "inboundEnabled": bool(config.get("inboundEnabled") or False),
        "lastUpdateId": int(config.get("lastUpdateId") or 0),
    }


def validate_telegram(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    status = telegram_status(workspace)
    if not status["enabled"] and not status["inboundEnabled"]:
        warnings.append("telegram onboarding is not enabled")
        return errors, warnings
    if status["enabled"] and not status["chatId"]:
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


def telegram_api_request(workspace: Workspace, method: str, payload: dict[str, Any] | None = None, timeout: int = 35) -> dict[str, Any]:
    status = telegram_status(workspace)
    token = os.getenv(str(status["botTokenEnv"]) or "")
    if not token:
        raise ValueError(f"telegram bot token environment variable is not set: {status['botTokenEnv']}")
    data = urlencode(payload or {}).encode("utf-8")
    request = Request(f"https://api.telegram.org/bot{token}/{method}", data=data, method="POST")
    with urlopen(request, timeout=timeout) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    return parsed if isinstance(parsed, dict) else {}


def poll_telegram_once(workspace: Workspace, timeout: int = 0) -> dict[str, Any]:
    status = telegram_status(workspace)
    if not status["inboundEnabled"]:
        return {"enabled": False, "messages": []}
    offset = int(status.get("lastUpdateId") or 0) + 1 if int(status.get("lastUpdateId") or 0) else 0
    payload = {"timeout": int(timeout), "allowed_updates": json.dumps(["message"])}
    if offset:
        payload["offset"] = offset
    parsed = telegram_api_request(workspace, "getUpdates", payload, timeout=max(5, int(timeout) + 5))
    messages: list[dict[str, Any]] = []
    max_update = int(status.get("lastUpdateId") or 0)
    for update in parsed.get("result") or []:
        if not isinstance(update, dict):
            continue
        update_id = int(update.get("update_id") or 0)
        max_update = max(max_update, update_id)
        message = update.get("message") if isinstance(update.get("message"), dict) else {}
        text = str(message.get("text") or "").strip()
        chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
        if not text:
            continue
        record = {
            "updateId": str(update_id),
            "chatId": str(chat.get("id") or ""),
            "text": text,
            "memoryNote": "",
        }
        try:
            from .memory import memory_write_note

            note = memory_write_note(
                workspace,
                f"Telegram inbound {update_id}",
                text,
                kind="conversations",
                note_type="session",
                tags=["telegram", "inbound"],
                sources=[f"telegram:{update_id}"],
                confidence=0.7,
            )
            record["memoryNote"] = str(note.path)
        except Exception as exc:
            record["memoryError"] = str(exc)
        messages.append(record)
    if max_update:
        config = telegram_config(workspace)
        config["lastUpdateId"] = max_update
        workspace.save_config()
    return {"enabled": True, "messages": messages, "rawOk": bool(parsed.get("ok", False))}


def run_telegram_inbound(workspace: Workspace, poll_interval: int = 2) -> None:
    while True:
        poll_telegram_once(workspace, timeout=20)
        time.sleep(max(1, int(poll_interval)))
