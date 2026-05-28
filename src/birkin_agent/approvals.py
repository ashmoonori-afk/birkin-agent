from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
from typing import Any
from urllib.request import Request, urlopen

from .util import is_relative_to, slugify, utc_stamp, write_json
from .workspace import Workspace


DEFAULT_APPROVAL_CONFIG = {
    "autoApprove": ["memory", "skills"],
    "pendingPath": "approvals/pending",
    "historyPath": "approvals/history",
    "riskTiers": {
        "memory": "safe",
        "skills": "review",
        "file": "review",
        "shell": "dangerous",
        "external": "external",
        "telegram": "external",
        "schedule": "review",
        "cron": "review",
        "mail": "external",
        "calendar": "external",
        "payment": "irreversible",
        "delete": "irreversible",
    },
}

RISK_ORDER = {"safe": 0, "review": 1, "external": 2, "dangerous": 3, "irreversible": 4}


@dataclass
class ApprovalRecord:
    id: str
    category: str
    title: str
    description: str
    payload: dict[str, Any]
    origin: str
    status: str
    created: str
    path: Path
    risk_tier: str = "review"
    evidence: list[dict[str, str]] | None = None
    resources: list[str] | None = None
    dry_run: str = ""
    rollback: str = ""


def approval_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("approvals", {})
    for key, value in DEFAULT_APPROVAL_CONFIG.items():
        if key not in config:
            config[key] = json.loads(json.dumps(value)) if isinstance(value, (dict, list)) else value
    return config


def pending_dir(workspace: Workspace) -> Path:
    path = workspace.rel(str(approval_config(workspace).get("pendingPath") or "approvals/pending"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def history_dir(workspace: Workspace) -> Path:
    path = workspace.rel(str(approval_config(workspace).get("historyPath") or "approvals/history"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def auto_approved(workspace: Workspace, category: str, risk_tier: str = "review") -> bool:
    if RISK_ORDER.get(risk_tier, 99) > RISK_ORDER["safe"]:
        return False
    value = approval_config(workspace).get("autoApprove") or []
    return category in value if isinstance(value, list) else False


def risk_tier_for(workspace: Workspace, category: str, payload: dict[str, Any] | None = None) -> str:
    payload = payload or {}
    if category == "file" and str(payload.get("action") or "").lower() in {"delete", "remove"}:
        return "irreversible"
    if category == "shell":
        return "dangerous"
    tiers = approval_config(workspace).get("riskTiers")
    value = tiers.get(category) if isinstance(tiers, dict) else None
    return str(value or "review")


def affected_resources(category: str, payload: dict[str, Any]) -> list[str]:
    if category == "file":
        return [str(payload.get("path") or "")]
    if category == "shell":
        return [str(payload.get("cwd") or "."), str(payload.get("command") or "")]
    if category == "external":
        return [str(payload.get("url") or "")]
    if category == "telegram":
        return ["telegram", str(payload.get("message") or "")[:80]]
    if category in {"cron", "schedule", "scheduling"}:
        return [str(payload.get("name") or "schedule"), str(payload.get("action") or "")]
    return [category]


def dry_run_preview(category: str, payload: dict[str, Any]) -> str:
    if category == "file":
        action = str(payload.get("action") or "write")
        return f"{action} {payload.get('path') or ''} ({len(str(payload.get('content') or ''))} chars)"
    if category == "shell":
        return f"run `{payload.get('command') or ''}` in `{payload.get('cwd') or '.'}`"
    if category == "external":
        return f"fetch {payload.get('url') or ''}"
    if category == "telegram":
        return f"send Telegram message ({len(str(payload.get('message') or ''))} chars)"
    if category in {"cron", "schedule", "scheduling"}:
        return f"create schedule {payload.get('name') or ''} at {payload.get('hour', '')}:{payload.get('minute', '')}"
    return f"approve {category}"


def rollback_hint(category: str, payload: dict[str, Any]) -> str:
    if category == "file":
        return "Restore or delete the written file from approval history."
    if category == "schedule":
        return "Remove the schedule entry from schedules/jobs.json."
    if category in {"telegram", "external"}:
        return "External delivery cannot be fully rolled back; record correction in memory."
    if category == "shell":
        return "Rollback depends on command side effects; inspect stdout/stderr and run a compensating action."
    return "No rollback handler registered."


def add_pending(
    workspace: Workspace,
    *,
    category: str,
    title: str,
    description: str,
    payload: dict[str, Any] | None = None,
    origin: str = "agent-runtime",
    risk_tier: str | None = None,
    evidence: list[dict[str, str]] | None = None,
    resources: list[str] | None = None,
    dry_run: str = "",
    rollback: str = "",
) -> ApprovalRecord:
    category = slugify(category)
    payload = payload or {}
    risk_tier = risk_tier or risk_tier_for(workspace, category, payload)
    record_id = f"{utc_stamp()}-{category}-{slugify(title)[:60]}"
    body = {
        "id": record_id,
        "category": category,
        "title": title.strip() or category,
        "description": description.strip(),
        "payload": payload,
        "origin": origin,
        "status": "pending",
        "created": utc_stamp(),
        "riskTier": risk_tier,
        "evidence": evidence or [],
        "resources": resources or affected_resources(category, payload),
        "dryRun": dry_run or dry_run_preview(category, payload),
        "rollback": rollback or rollback_hint(category, payload),
    }
    path = pending_dir(workspace) / f"{record_id}.json"
    suffix = 2
    while path.exists():
        path = pending_dir(workspace) / f"{record_id}-{suffix}.json"
        body["id"] = f"{record_id}-{suffix}"
        suffix += 1
    write_json(path, body)
    try:
        from .reliability import log_reliability_event

        log_reliability_event(
            workspace,
            stage="approval",
            status="pending",
            resource=record_id,
            message=f"{risk_tier} approval queued: {title}",
            evidence=evidence or [],
            metadata={"category": category, "origin": origin},
        )
    except Exception:
        pass
    return approval_from_payload(path, body)


def propose_action(
    workspace: Workspace,
    *,
    category: str,
    title: str,
    description: str,
    payload: dict[str, Any] | None = None,
    origin: str = "agent-runtime",
    risk_tier: str | None = None,
    evidence: list[dict[str, str]] | None = None,
    resources: list[str] | None = None,
    dry_run: str = "",
    rollback: str = "",
    explicit_user: bool = False,
) -> dict[str, Any]:
    payload = payload or {}
    risk_tier = risk_tier or risk_tier_for(workspace, category, payload)
    if explicit_user or auto_approved(workspace, category, risk_tier):
        result = execute_action(workspace, category, payload)
        return {"auto": True, "status": "applied", "riskTier": risk_tier, "result": result}
    record = add_pending(
        workspace,
        category=category,
        title=title,
        description=description,
        payload=payload,
        origin=origin,
        risk_tier=risk_tier,
        evidence=evidence,
        resources=resources,
        dry_run=dry_run,
        rollback=rollback,
    )
    return {"auto": False, "status": "pending", "id": record.id, "riskTier": record.risk_tier}


def read_record(path: Path) -> ApprovalRecord | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return approval_from_payload(path, payload)


def approval_from_payload(path: Path, payload: dict[str, Any]) -> ApprovalRecord:
    raw_payload = payload.get("payload")
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), list) else []
    resources = payload.get("resources") if isinstance(payload.get("resources"), list) else []
    return ApprovalRecord(
        id=str(payload.get("id") or path.stem),
        category=str(payload.get("category") or ""),
        title=str(payload.get("title") or ""),
        description=str(payload.get("description") or ""),
        payload=raw_payload if isinstance(raw_payload, dict) else {},
        origin=str(payload.get("origin") or ""),
        status=str(payload.get("status") or "pending"),
        created=str(payload.get("created") or ""),
        path=path,
        risk_tier=str(payload.get("riskTier") or "review"),
        evidence=[item for item in evidence if isinstance(item, dict)],
        resources=[str(item) for item in resources],
        dry_run=str(payload.get("dryRun") or ""),
        rollback=str(payload.get("rollback") or ""),
    )


def list_pending(workspace: Workspace) -> list[ApprovalRecord]:
    records: list[ApprovalRecord] = []
    for path in sorted(pending_dir(workspace).glob("*.json"), key=lambda item: item.name):
        record = read_record(path)
        if record:
            records.append(record)
    return records


def approval_rows(workspace: Workspace) -> list[dict[str, str]]:
    return [
        {
            "id": record.id,
            "category": record.category,
            "title": record.title,
            "origin": record.origin,
            "status": record.status,
            "riskTier": record.risk_tier,
            "evidence": str(len(record.evidence or [])),
            "resources": ", ".join(record.resources or []),
            "dryRun": record.dry_run,
            "rollback": record.rollback,
            "created": record.created,
            "description": record.description,
        }
        for record in list_pending(workspace)
    ]


def find_pending(workspace: Workspace, approval_id: str) -> ApprovalRecord:
    for record in list_pending(workspace):
        if record.id == approval_id:
            return record
    raise KeyError(f"pending approval not found: {approval_id}")


def resolve_approval(workspace: Workspace, approval_id: str, status: str, result: str = "") -> dict[str, Any]:
    record = find_pending(workspace, approval_id)
    payload = {
        "id": record.id,
        "category": record.category,
        "title": record.title,
        "description": record.description,
        "payload": record.payload,
        "origin": record.origin,
        "status": status,
        "created": record.created,
        "riskTier": record.risk_tier,
        "evidence": record.evidence or [],
        "resources": record.resources or [],
        "dryRun": record.dry_run,
        "rollback": record.rollback,
        "resolved": utc_stamp(),
        "result": result,
    }
    target = history_dir(workspace) / f"{record.id}-{status}.json"
    write_json(target, payload)
    record.path.unlink(missing_ok=True)
    try:
        from .reliability import log_reliability_event

        log_reliability_event(
            workspace,
            stage="approval",
            status=status,
            resource=record.id,
            message=result or status,
            evidence=record.evidence or [],
            metadata={"category": record.category, "riskTier": record.risk_tier},
        )
    except Exception:
        pass
    return payload


def approve(workspace: Workspace, approval_id: str) -> dict[str, Any]:
    record = find_pending(workspace, approval_id)
    result = execute_action(workspace, record.category, record.payload)
    return resolve_approval(workspace, approval_id, "approved", result)


def reject(workspace: Workspace, approval_id: str) -> dict[str, Any]:
    return resolve_approval(workspace, approval_id, "rejected", "rejected by user")


def execute_action(workspace: Workspace, category: str, payload: dict[str, Any]) -> str:
    try:
        if category == "shell":
            result = execute_shell(workspace, payload)
        elif category == "telegram":
            from .telegram import send_telegram_message

            delivered = send_telegram_message(workspace, str(payload.get("message") or ""))
            result = delivered.get("stdout") or delivered.get("stderr") or f"telegram returncode={delivered.get('returncode')}"
        elif category in {"cron", "schedule", "scheduling"}:
            from .scheduler import add_schedule

            schedule = add_schedule(workspace, payload)
            result = f"scheduled {schedule['id']}"
        elif category == "external":
            result = execute_external_fetch(payload)
        elif category == "file":
            result = execute_file_action(workspace, payload)
        elif category in {"memory", "skills"}:
            result = "safe action already applied"
        else:
            result = f"approved {category}; no executor is registered"
        try:
            from .reliability import log_reliability_event

            log_reliability_event(workspace, stage="delivery", status="ok", resource=category, message=result)
        except Exception:
            pass
        return result
    except Exception as exc:
        try:
            from .reliability import log_reliability_event

            log_reliability_event(workspace, stage="delivery", status="failed", resource=category, message=str(exc))
        except Exception:
            pass
        raise


def execute_shell(workspace: Workspace, payload: dict[str, Any]) -> str:
    command = str(payload.get("command") or "").strip()
    if not command:
        raise ValueError("shell approval payload requires command")
    cwd_raw = str(payload.get("cwd") or ".")
    cwd = workspace.rel(cwd_raw) if not Path(cwd_raw).is_absolute() else Path(cwd_raw).resolve()
    if not is_relative_to(cwd, workspace.root):
        raise ValueError("approved shell cwd must stay inside workspace")
    timeout = int(payload.get("timeout") or 120)
    completed = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    output = stdout or stderr or "(no output)"
    return f"exit {completed.returncode}: {output[:1000]}"


def execute_file_action(workspace: Workspace, payload: dict[str, Any]) -> str:
    rel_path = str(payload.get("path") or "").strip()
    content = str(payload.get("content") or "")
    if not rel_path:
        raise ValueError("file approval payload requires path")
    path = workspace.rel(rel_path)
    action = str(payload.get("action") or "write").lower()
    if action in {"delete", "remove"}:
        if path.exists():
            path.unlink()
            return f"deleted {path.relative_to(workspace.root)}"
        return f"delete skipped; {path.relative_to(workspace.root)} did not exist"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"wrote {path.relative_to(workspace.root)}"


def execute_file_write(workspace: Workspace, payload: dict[str, Any]) -> str:
    return execute_file_action(workspace, payload)


def execute_external_fetch(payload: dict[str, Any]) -> str:
    url = str(payload.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("external approval payload requires http or https url")
    request = Request(url, headers={"user-agent": "birkin-codex/0"})
    with urlopen(request, timeout=int(payload.get("timeout") or 30)) as response:
        data = response.read(200_000)
    text = data.decode("utf-8", errors="replace")
    return text[:5000] or "(empty response)"
