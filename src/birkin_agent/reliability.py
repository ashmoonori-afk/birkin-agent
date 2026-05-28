from __future__ import annotations

import json
from typing import Any

from .util import slugify, utc_stamp
from .workspace import Workspace


DEFAULT_RELIABILITY_CONFIG = {
    "eventsPath": "reliability/events.jsonl",
    "budgets": {
        "perRunTokenLimit": 120000,
        "dailyTokenLimit": 500000,
        "monthlyTokenLimit": 5000000,
        "warnAtPct": 80,
    },
}


def reliability_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("reliability", {})
    for key, value in DEFAULT_RELIABILITY_CONFIG.items():
        config.setdefault(key, value.copy() if isinstance(value, dict) else value)
    return config


def reliability_log_path(workspace: Workspace):
    path = workspace.rel(str(reliability_config(workspace).get("eventsPath") or "reliability/events.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def log_reliability_event(
    workspace: Workspace,
    *,
    stage: str,
    status: str,
    trace_id: str = "",
    resource: str = "",
    message: str = "",
    evidence: Any = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "id": f"{utc_stamp()}-{slugify(stage)}-{slugify(resource or status)[:60]}",
        "timestamp": utc_stamp(),
        "traceId": trace_id or f"trace-{utc_stamp()}",
        "stage": stage,
        "status": status,
        "resource": resource,
        "message": message,
        "evidence": evidence or [],
        "metadata": metadata or {},
    }
    with reliability_log_path(workspace).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_reliability_events(workspace: Workspace, limit: int | None = None) -> list[dict[str, Any]]:
    path = reliability_log_path(workspace)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    rows = list(reversed(rows))
    return rows[:limit] if limit else rows


def reliability_rows(workspace: Workspace, limit: int = 50) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for event in read_reliability_events(workspace, limit=limit):
        rows.append(
            {
                "id": str(event.get("id") or ""),
                "timestamp": str(event.get("timestamp") or ""),
                "traceId": str(event.get("traceId") or ""),
                "stage": str(event.get("stage") or ""),
                "status": str(event.get("status") or ""),
                "resource": str(event.get("resource") or ""),
                "message": str(event.get("message") or ""),
            }
        )
    return rows


def trace_rows(workspace: Workspace, limit: int = 80) -> list[dict[str, str]]:
    rows = reliability_rows(workspace, limit=limit)
    stage_order = {
        "user": 0,
        "agent": 1,
        "tool": 2,
        "subagent": 3,
        "approval": 4,
        "delivery": 5,
        "result": 6,
    }
    return sorted(rows, key=lambda row: (row["traceId"], stage_order.get(row["stage"], 99), row["timestamp"]), reverse=True)


def delivery_rows(workspace: Workspace, limit: int = 50) -> list[dict[str, str]]:
    return [row for row in reliability_rows(workspace, limit=limit * 2) if row["stage"] == "delivery"][:limit]


def health_checks(workspace: Workspace) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, errors: list[str], warnings: list[str], detail: str) -> None:
        status = "error" if errors else "warning" if warnings else "ok"
        message = "; ".join(errors[:2] or warnings[:2]) or detail
        checks.append({"name": name, "status": status, "detail": message})

    from .api import validate_api
    from .gateway import validate_gateway
    from .ledger import ledger_summary
    from .memory import validate_memory
    from .models import validate_models
    from .morpheus import morpheus_status
    from .telegram import validate_telegram

    errors, warnings = validate_gateway(workspace)
    add("gateway", errors, warnings, "Gateway config is valid.")
    status = morpheus_status(workspace)
    add(
        "morpheus",
        [],
        [] if status.get("enabled") else ["Morpheus daemon is not enabled"],
        f"Morpheus scheduled for {status.get('hour', 4):02d}:{status.get('minute', 0):02d}.",
    )
    errors, warnings = validate_telegram(workspace)
    add("telegram", errors, warnings, "Telegram config is usable.")
    errors, warnings = validate_memory(workspace)
    add("memory", errors, warnings, "Obsidian memory is configured.")
    ledger = ledger_summary(workspace)
    add("ledger", [], [], f"{ledger.get('totals', {}).get('runs', 0)} ledger run(s) tracked.")
    errors, warnings = validate_models(workspace)
    add("models", errors, warnings, "Model profiles are valid.")
    errors, warnings = validate_api(workspace)
    add("api", errors, warnings, "API profiles are valid.")
    return checks


def budget_status(workspace: Workspace) -> dict[str, Any]:
    from .ledger import read_ledger

    budgets = reliability_config(workspace).get("budgets")
    budgets = budgets if isinstance(budgets, dict) else {}
    per_run_limit = int(budgets.get("perRunTokenLimit") or 120000)
    daily_limit = int(budgets.get("dailyTokenLimit") or 500000)
    monthly_limit = int(budgets.get("monthlyTokenLimit") or 5000000)
    warn_at = int(budgets.get("warnAtPct") or 80)
    rows = read_ledger(workspace)
    today = utc_stamp()[:10]
    month = utc_stamp()[:7]
    per_run = max((int(row.get("providerTotalTokens") or row.get("estimatedTokens") or 0) for row in rows), default=0)
    daily = sum(
        int(row.get("providerTotalTokens") or row.get("estimatedTokens") or 0)
        for row in rows
        if str(row.get("timestamp") or "").startswith(today)
    )
    monthly = sum(
        int(row.get("providerTotalTokens") or row.get("estimatedTokens") or 0)
        for row in rows
        if str(row.get("timestamp") or "").startswith(month)
    )
    warnings = []
    for label, used, limit in [
        ("per-run", per_run, per_run_limit),
        ("daily", daily, daily_limit),
        ("monthly", monthly, monthly_limit),
    ]:
        if limit > 0 and used * 100 >= limit * warn_at:
            warnings.append(f"{label} token usage is {used}/{limit}")
    return {
        "perRun": {"used": per_run, "limit": per_run_limit},
        "daily": {"used": daily, "limit": daily_limit},
        "monthly": {"used": monthly, "limit": monthly_limit},
        "warnAtPct": warn_at,
        "warnings": warnings,
        "modelRouting": workspace.config.get("models", {}).get("default", "packet"),
    }


def silent_failure_warnings(workspace: Workspace) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for row in delivery_rows(workspace):
        if row["status"] in {"failed", "error", "timeout"}:
            warnings.append({"severity": "critical", "source": "delivery", "message": row["message"] or row["resource"]})
    budget = budget_status(workspace)
    for item in budget.get("warnings") or []:
        warnings.append({"severity": "warning", "source": "budget", "message": str(item)})
    return warnings
