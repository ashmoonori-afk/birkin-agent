from __future__ import annotations

from datetime import datetime
import time
from typing import Any

from .util import slugify, utc_stamp, write_json
from .workspace import Workspace


DEFAULT_SCHEDULER_CONFIG = {
    "path": "schedules/jobs.json",
    "statusPath": "schedules/daemon-status.json",
}


def scheduler_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("scheduler", {})
    for key, value in DEFAULT_SCHEDULER_CONFIG.items():
        config.setdefault(key, value)
    return config


def schedule_path(workspace: Workspace):
    return workspace.rel(str(scheduler_config(workspace).get("path") or "schedules/jobs.json"))


def status_path(workspace: Workspace):
    return workspace.rel(str(scheduler_config(workspace).get("statusPath") or "schedules/daemon-status.json"))


def list_schedules(workspace: Workspace) -> list[dict[str, Any]]:
    path = schedule_path(workspace)
    if not path.exists():
        return []
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return payload if isinstance(payload, list) else []


def schedule_rows(workspace: Workspace) -> list[dict[str, str]]:
    return [
        {
            "id": str(item.get("id") or ""),
            "name": str(item.get("name") or ""),
            "hour": str(item.get("hour") or ""),
            "minute": str(item.get("minute") or "0"),
            "action": str(item.get("action") or item.get("type") or ""),
            "created": str(item.get("created") or ""),
        }
        for item in list_schedules(workspace)
    ]


def add_schedule(workspace: Workspace, payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or payload.get("title") or "schedule").strip()
    hour = int(payload.get("hour") if payload.get("hour") is not None else 4)
    minute = int(payload.get("minute") if payload.get("minute") is not None else 0)
    if hour < 0 or hour > 23:
        raise ValueError("schedule hour must be between 0 and 23")
    if minute < 0 or minute > 59:
        raise ValueError("schedule minute must be between 0 and 59")
    schedules = list_schedules(workspace)
    item = {
        "id": f"{utc_stamp()}-{slugify(name)[:60]}",
        "name": name,
        "hour": hour,
        "minute": minute,
        "action": str(payload.get("action") or payload.get("type") or "prompt"),
        "payload": payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
        "created": utc_stamp(),
    }
    schedules.append(item)
    write_json(schedule_path(workspace), schedules)
    return item


def daemon_status(workspace: Workspace) -> dict[str, Any]:
    path = status_path(workspace)
    if not path.exists():
        return {"running": False, "lastCheck": "", "lastMorpheus": "", "path": str(path)}
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"running": False, "lastCheck": "", "lastMorpheus": "", "path": str(path)}
    if isinstance(payload, dict):
        payload["path"] = str(path)
        return payload
    return {"running": False, "lastCheck": "", "lastMorpheus": "", "path": str(path)}


def write_daemon_status(workspace: Workspace, payload: dict[str, Any]) -> None:
    payload = dict(payload)
    payload["path"] = str(status_path(workspace))
    write_json(status_path(workspace), payload)


def run_daemon(workspace: Workspace, *, once: bool = False, interval_seconds: int = 60) -> None:
    from .morpheus import morpheus_config, run_morpheus

    last_day = ""
    while True:
        cfg = morpheus_config(workspace)
        now = datetime.now()
        should_run = (
            now.hour == int(cfg.get("hour") or 4)
            and now.minute == int(cfg.get("minute") or 0)
            and now.strftime("%Y-%m-%d") != last_day
        )
        status = daemon_status(workspace)
        status.update({"running": True, "lastCheck": utc_stamp()})
        if should_run or once:
            result = run_morpheus(workspace, dry_run=bool(cfg.get("dryRun", True)))
            last_day = now.strftime("%Y-%m-%d")
            status["lastMorpheus"] = utc_stamp()
            status["lastResult"] = result
        write_daemon_status(workspace, status)
        if once:
            return
        time.sleep(max(5, int(interval_seconds)))
