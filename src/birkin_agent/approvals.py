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
}


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


def approval_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("approvals", {})
    for key, value in DEFAULT_APPROVAL_CONFIG.items():
        if key not in config:
            config[key] = list(value) if isinstance(value, list) else value
    return config


def pending_dir(workspace: Workspace) -> Path:
    path = workspace.rel(str(approval_config(workspace).get("pendingPath") or "approvals/pending"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def history_dir(workspace: Workspace) -> Path:
    path = workspace.rel(str(approval_config(workspace).get("historyPath") or "approvals/history"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def auto_approved(workspace: Workspace, category: str) -> bool:
    value = approval_config(workspace).get("autoApprove") or []
    return category in value if isinstance(value, list) else False


def add_pending(
    workspace: Workspace,
    *,
    category: str,
    title: str,
    description: str,
    payload: dict[str, Any] | None = None,
    origin: str = "agent-runtime",
) -> ApprovalRecord:
    category = slugify(category)
    record_id = f"{utc_stamp()}-{category}-{slugify(title)[:60]}"
    body = {
        "id": record_id,
        "category": category,
        "title": title.strip() or category,
        "description": description.strip(),
        "payload": payload or {},
        "origin": origin,
        "status": "pending",
        "created": utc_stamp(),
    }
    path = pending_dir(workspace) / f"{record_id}.json"
    suffix = 2
    while path.exists():
        path = pending_dir(workspace) / f"{record_id}-{suffix}.json"
        body["id"] = f"{record_id}-{suffix}"
        suffix += 1
    write_json(path, body)
    return approval_from_payload(path, body)


def propose_action(
    workspace: Workspace,
    *,
    category: str,
    title: str,
    description: str,
    payload: dict[str, Any] | None = None,
    origin: str = "agent-runtime",
) -> dict[str, Any]:
    if auto_approved(workspace, category):
        result = execute_action(workspace, category, payload or {})
        return {"auto": True, "status": "applied", "result": result}
    record = add_pending(
        workspace,
        category=category,
        title=title,
        description=description,
        payload=payload or {},
        origin=origin,
    )
    return {"auto": False, "status": "pending", "id": record.id}


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
        "resolved": utc_stamp(),
        "result": result,
    }
    target = history_dir(workspace) / f"{record.id}-{status}.json"
    write_json(target, payload)
    record.path.unlink(missing_ok=True)
    return payload


def approve(workspace: Workspace, approval_id: str) -> dict[str, Any]:
    record = find_pending(workspace, approval_id)
    result = execute_action(workspace, record.category, record.payload)
    return resolve_approval(workspace, approval_id, "approved", result)


def reject(workspace: Workspace, approval_id: str) -> dict[str, Any]:
    return resolve_approval(workspace, approval_id, "rejected", "rejected by user")


def execute_action(workspace: Workspace, category: str, payload: dict[str, Any]) -> str:
    if category == "shell":
        return execute_shell(workspace, payload)
    if category == "telegram":
        from .telegram import send_telegram_message

        result = send_telegram_message(workspace, str(payload.get("message") or ""))
        return result.get("stdout") or result.get("stderr") or f"telegram returncode={result.get('returncode')}"
    if category in {"cron", "schedule", "scheduling"}:
        from .scheduler import add_schedule

        schedule = add_schedule(workspace, payload)
        return f"scheduled {schedule['id']}"
    if category == "external":
        return execute_external_fetch(payload)
    if category == "file":
        return execute_file_write(workspace, payload)
    if category in {"memory", "skills"}:
        return "safe action already applied"
    return f"approved {category}; no executor is registered"


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


def execute_file_write(workspace: Workspace, payload: dict[str, Any]) -> str:
    rel_path = str(payload.get("path") or "").strip()
    content = str(payload.get("content") or "")
    if not rel_path:
        raise ValueError("file approval payload requires path")
    path = workspace.rel(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"wrote {path.relative_to(workspace.root)}"


def execute_external_fetch(payload: dict[str, Any]) -> str:
    url = str(payload.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("external approval payload requires http or https url")
    request = Request(url, headers={"user-agent": "birkin-codex/0"})
    with urlopen(request, timeout=int(payload.get("timeout") or 30)) as response:
        data = response.read(200_000)
    text = data.decode("utf-8", errors="replace")
    return text[:5000] or "(empty response)"
