from __future__ import annotations

from typing import Any

from .memory import configure_obsidian_vault, memory_status
from .models import default_model_id, model_rows, use_model_profile
from .telegram import configure_telegram, telegram_status
from .workspace import Workspace


def setup_wizard(
    workspace: Workspace,
    model: str | None = None,
    obsidian_vault: str | None = None,
    telegram_chat_id: str | None = None,
    telegram_token_env: str | None = None,
    enable_telegram: bool | None = None,
    enable_telegram_inbound: bool | None = None,
    interactive: bool = True,
) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    selected_model = model
    if interactive and not selected_model:
        selected_model = prompt_model(workspace)
    if selected_model:
        use_model_profile(workspace, selected_model)
        rows.append({"step": "model", "status": "ok", "detail": f"default model set to {selected_model}"})
    else:
        rows.append({"step": "model", "status": "ok", "detail": f"default model remains {default_model_id(workspace)}"})

    selected_vault = obsidian_vault
    if interactive and not selected_vault:
        default_vault = str(workspace.config.get("memory", {}).get("vaultPath") or "memory/obsidian-vault")
        selected_vault = input(f"Obsidian vault path [{default_vault}]: ").strip() or default_vault
    if selected_vault:
        configure_obsidian_vault(workspace, selected_vault, allow_external=False)
        rows.append({"step": "memory", "status": "ok", "detail": f"Obsidian vault set to {memory_status(workspace)['vaultPath']}"})

    token_env = telegram_token_env or "TELEGRAM_BOT_TOKEN"
    chat_id = telegram_chat_id or ""
    enabled = bool(enable_telegram) if enable_telegram is not None else False
    inbound_enabled = bool(enable_telegram_inbound) if enable_telegram_inbound is not None else False
    if interactive and telegram_chat_id is None:
        answer = input("Enable Telegram onboarding? [y/N]: ").strip().lower()
        enabled = answer in {"y", "yes"}
        if enabled:
            token_env = input(f"Telegram bot token env [{token_env}]: ").strip() or token_env
            chat_id = input("Telegram chat id: ").strip()
            inbound_answer = input("Enable Telegram inbound long polling? [y/N]: ").strip().lower()
            inbound_enabled = inbound_answer in {"y", "yes"}
    if enabled or telegram_chat_id is not None:
        configure_telegram(workspace, chat_id, token_env, enabled=enabled, inbound_enabled=inbound_enabled)
        status = telegram_status(workspace)
        detail = f"enabled={status['enabled']} inbound={status['inboundEnabled']} tokenEnv={status['botTokenEnv']} chatId={'set' if status['chatId'] else 'missing'}"
        rows.append({"step": "telegram", "status": "ok" if status["chatId"] or not enabled else "warning", "detail": detail})
    else:
        rows.append({"step": "telegram", "status": "warning", "detail": "telegram onboarding skipped"})

    return {"status": "warning" if any(row["status"] == "warning" for row in rows) else "ok", "steps": rows}


def prompt_model(workspace: Workspace) -> str:
    rows = model_rows(workspace)
    print("Available model profiles:")
    for index, row in enumerate(rows, start=1):
        marker = " default" if row["default"] == "yes" else ""
        print(f"  {index}. {row['id']} ({row['runner']}/{row['provider']}){marker}")
    answer = input(f"Choose model [{default_model_id(workspace)}]: ").strip()
    if not answer:
        return default_model_id(workspace)
    if answer.isdigit():
        offset = int(answer) - 1
        if offset < 0 or offset >= len(rows):
            raise ValueError("model selection is out of range")
        return rows[offset]["id"]
    return answer
