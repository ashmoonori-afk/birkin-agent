from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .agents import validate_agents
from .api import validate_api
from .approvals import approval_rows
from .auth import auth_rows, validate_auth
from .gateway import gateway_info, validate_gateway
from .ledger import ledger_summary
from .memory import memory_status, validate_memory
from .models import model_rows, validate_models
from .morpheus import morpheus_status
from .presets import is_lite
from .runtime_deps import validate_runtime_dependencies
from .scheduler import schedule_rows
from .skills import skill_config_rows, skill_rows, validate_skills
from .telegram import telegram_status, validate_telegram
from .workspace import Workspace


@dataclass
class SetupCheck:
    step: str
    status: str
    detail: str
    command: str


def setup_checks(workspace: Workspace, advanced: bool = False) -> list[SetupCheck]:
    rows: list[SetupCheck] = []
    lite = is_lite(workspace.config) and not advanced
    mode_detail = (
        "Lite mode keeps the default setup focused on chat, memory, skills, and local runs."
        if lite
        else "Full setup includes auth, API, gateway, Telegram, approvals, Morpheus, schedules, and ledger status."
    )
    add_check(
        rows,
        "mode",
        [],
        [],
        mode_detail,
        "birkin-codex mode status",
    )
    runtime_errors, runtime_warnings = validate_runtime_dependencies(workspace)
    add_check(
        rows,
        "runtime",
        runtime_errors,
        runtime_warnings,
        "Lite core has no runtime package dependencies.",
        "birkin-codex doctor",
    )
    workspace_errors, workspace_warnings = workspace.doctor()
    add_check(
        rows,
        "workspace",
        workspace_errors,
        workspace_warnings,
        "Workspace files, prompt files, and configured roots are present.",
        "birkin-codex doctor",
    )
    model_errors, model_warnings = validate_models(workspace)
    add_check(
        rows,
        "models",
        model_errors,
        model_warnings,
        f"{len(model_rows(workspace))} model profiles configured.",
        "birkin-codex model list",
    )
    memory_errors, memory_warnings = validate_memory(workspace)
    memory = memory_status(workspace)
    add_check(
        rows,
        "memory",
        memory_errors,
        memory_warnings,
        f"Obsidian memory vault: {memory['vaultPath']}.",
        "birkin-codex memory status",
    )
    skill_errors, skill_warnings = validate_skills(workspace)
    skills = skill_rows(workspace)
    enabled = sum(1 for row in skills if row["enabled"] == "yes")
    add_check(
        rows,
        "skills",
        skill_errors,
        skill_warnings,
        f"{enabled}/{len(skills)} skills are enabled and eligible.",
        "birkin-codex skills validate",
    )
    agent_errors, agent_warnings = validate_agents(workspace)
    add_check(
        rows,
        "agents",
        agent_errors,
        agent_warnings,
        "Agent roles and skill allowlists are configured.",
        "birkin-codex agents list",
    )
    chat_errors = []
    agent_ids = {str(raw.get("id") or "") for raw in workspace.config.get("agents", {}).get("list", [])}
    if "chat" not in agent_ids:
        chat_errors.append("chat agent is not configured")
    add_check(
        rows,
        "chat",
        chat_errors,
        [],
        "Chat agent and dashboard chat API are available.",
        "birkin-codex web --port 8765",
    )
    if lite:
        return rows

    auth_errors, auth_warnings = validate_auth(workspace)
    auth = auth_rows(workspace)
    auth_detail = f"{len(auth)} auth profiles configured."
    if any(row["available"] == "yes" for row in auth):
        auth_detail += " At least one local CLI auth binary is available."
    add_check(rows, "auth", auth_errors, auth_warnings, auth_detail, "birkin-codex auth list")
    api_errors, api_warnings = validate_api(workspace)
    add_check(
        rows,
        "api",
        api_errors,
        api_warnings,
        "OpenAI-compatible API profiles are configured.",
        "birkin-codex api list",
    )
    gateway_errors, gateway_warnings = validate_gateway(workspace)
    info = gateway_info(workspace)
    add_check(
        rows,
        "gateway",
        gateway_errors,
        gateway_warnings,
        f"Gateway configured for {info['host']}:{info['port']}.",
        "birkin-codex gateway status",
    )
    telegram_errors, telegram_warnings = validate_telegram(workspace)
    telegram = telegram_status(workspace)
    add_check(
        rows,
        "telegram",
        telegram_errors,
        telegram_warnings,
        f"Telegram enabled={telegram['enabled']} chatId={'set' if telegram['chatId'] else 'missing'}.",
        "birkin-codex telegram status",
    )
    ledger = ledger_summary(workspace)
    add_check(
        rows,
        "ledger",
        [],
        [],
        f"Usage ledger has {ledger['totals']['runs']} entries at {ledger['path']}.",
        "birkin-codex ledger summary",
    )
    approvals = approval_rows(workspace)
    add_check(
        rows,
        "approvals",
        [],
        [f"{len(approvals)} pending approval(s)"] if approvals else [],
        "Consequential shell, web, Telegram, and schedule actions are approval-gated.",
        "birkin-codex approvals list",
    )
    morpheus = morpheus_status(workspace)
    add_check(
        rows,
        "morpheus",
        [],
        [] if morpheus["enabled"] else ["Morpheus daemon is not enabled"],
        f"Morpheus configured for {morpheus['hour']:02d}:{morpheus['minute']:02d}.",
        "birkin-codex morpheus --dry-run",
    )
    schedules = schedule_rows(workspace)
    add_check(
        rows,
        "schedules",
        [],
        [],
        f"{len(schedules)} approved schedule(s) stored.",
        "birkin-codex daemon status",
    )
    return rows


def add_check(
    rows: list[SetupCheck],
    step: str,
    errors: list[str],
    warnings: list[str],
    detail: str,
    command: str,
) -> None:
    status = "error" if errors else "warning" if warnings else "ok"
    if errors:
        detail = "; ".join(errors[:2])
    elif warnings:
        detail = detail + " Warning: " + "; ".join(warnings[:2])
    rows.append(SetupCheck(step, status, detail, command))


def setup_rows(workspace: Workspace, advanced: bool = False) -> list[dict[str, str]]:
    return [
        {
            "step": item.step,
            "status": item.status,
            "detail": item.detail,
            "command": item.command,
        }
        for item in setup_checks(workspace, advanced=advanced)
    ]


def setup_report(workspace: Workspace, advanced: bool = False) -> dict[str, Any]:
    rows = setup_rows(workspace, advanced=advanced)
    status = "error" if any(row["status"] == "error" for row in rows) else "warning" if any(
        row["status"] == "warning" for row in rows
    ) else "ok"
    return {
        "status": status,
        "checks": rows,
        "skillConfig": skill_config_rows(workspace),
    }
