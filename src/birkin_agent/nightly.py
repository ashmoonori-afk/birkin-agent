from __future__ import annotations

from datetime import datetime
import json
import subprocess
from typing import Any

from .approvals import propose_action
from .improve import collect_signals
from .ledger import ledger_rows, ledger_summary
from .memory import memory_search, memory_status, memory_write_note
from .skills import create_skill
from .util import slugify, utc_stamp, write_json
from .workspace import Workspace


DEFAULT_MORPHEUS_CONFIG = {
    "enabled": False,
    "hour": 4,
    "minute": 0,
    "timezone": "local",
    "dryRun": True,
}


def morpheus_config(workspace: Workspace) -> dict[str, Any]:
    legacy = workspace.config.get("nightly") if isinstance(workspace.config.get("nightly"), dict) else {}
    config = workspace.config.setdefault("morpheus", {})
    if isinstance(legacy, dict):
        for key, value in legacy.items():
            config.setdefault(key, value)
    for key, value in DEFAULT_MORPHEUS_CONFIG.items():
        config.setdefault(key, value)
    return config


def morpheus_status(workspace: Workspace) -> dict[str, Any]:
    config = morpheus_config(workspace)
    latest = latest_morpheus_record(workspace)
    return {
        "enabled": bool(config.get("enabled") or False),
        "hour": int(config.get("hour") or 4),
        "minute": int(config.get("minute") or 0),
        "dryRun": bool(config.get("dryRun", True)),
        "latestRun": str(latest) if latest else "",
    }


def run_morpheus(workspace: Workspace, *, dry_run: bool = False) -> dict[str, Any]:
    snapshot = gather_nightly_context(workspace)
    actions: list[dict[str, Any]] = []
    if not dry_run:
        note = memory_write_note(
            workspace,
            f"Morpheus self-improvement {datetime.now().strftime('%Y-%m-%d')}",
            render_morpheus_memory(snapshot),
            kind="runs",
            note_type="run",
            tags=["morpheus", "self-improvement"],
            links=["Birkin Ledger", "Birkin Skills"],
            confidence=0.75,
            sources=["morpheus"],
            append=True,
        )
        actions.append({"type": "memory", "path": str(note.path)})
        skill_path = ensure_morpheus_skill(workspace, snapshot)
        if skill_path:
            actions.append({"type": "skill", "path": str(skill_path)})
        if not schedule_exists(workspace):
            proposal = propose_action(
                workspace,
                category="schedule",
                title="Daily Birkin Morpheus self-improvement at 04:00",
                description="Enable the portable daemon to run the Morpheus review at 04:00.",
                payload={"name": "birkin-morpheus", "hour": 4, "minute": 0, "action": "morpheus", "payload": {"dryRun": True}},
                origin="morpheus",
            )
            actions.append({"type": "approval", "proposal": proposal})

    result = {
        "timestamp": utc_stamp(),
        "status": "dry-run" if dry_run else "ok",
        "summary": summarize_snapshot(snapshot, dry_run),
        "dryRun": dry_run,
        "context": snapshot,
        "actions": actions,
    }
    path = workspace.rel("runs", f"{utc_stamp()}_morpheus.json")
    write_json(path, result)
    result["record"] = str(path)
    return result


def latest_morpheus_record(workspace: Workspace):
    runs = workspace.rel("runs")
    if not runs.exists():
        return None
    matches = sorted([*runs.glob("*_morpheus.json"), *runs.glob("*_nightly.json")], key=lambda path: path.name, reverse=True)
    return matches[0] if matches else None


def gather_nightly_context(workspace: Workspace) -> dict[str, Any]:
    runs = []
    run_root = workspace.rel("runs")
    if run_root.exists():
        for path in sorted(run_root.glob("*.json"), key=lambda item: item.name, reverse=True)[:20]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            runs.append(
                {
                    "record": str(path.relative_to(workspace.root)),
                    "agent": str(payload.get("agent") or ""),
                    "status": str(payload.get("status") or ""),
                    "summary": str(payload.get("summary") or "")[:300],
                }
            )
    memory = memory_status(workspace)
    memory_hits = memory_search(workspace, "USER_CORRECTION LESSON FAILED error feedback", limit=10)
    signals = collect_signals(workspace)[:20]
    changed = list_changed_files(workspace)
    ledger = ledger_summary(workspace)
    return {
        "runs": runs,
        "memory": memory,
        "memoryHits": memory_hits,
        "signals": signals,
        "changedFiles": changed,
        "ledger": ledger,
        "ledgerRows": ledger_rows(workspace, limit=10),
    }


def list_changed_files(workspace: Workspace) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=workspace.root,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()][:80]


def render_morpheus_memory(snapshot: dict[str, Any]) -> str:
    lines = ["# Morpheus Self-Improvement", ""]
    ledger = snapshot.get("ledger") if isinstance(snapshot.get("ledger"), dict) else {}
    totals = ledger.get("totals") if isinstance(ledger.get("totals"), dict) else {}
    lines.append(f"- Runs tracked: `{totals.get('runs', 0)}`")
    lines.append(f"- Memory notes: `{snapshot.get('memory', {}).get('noteCount', 0)}`")
    lines.append(f"- Signals found: `{len(snapshot.get('signals') or [])}`")
    lines.append("")
    lines.append("## Recent Runs")
    for item in snapshot.get("runs") or []:
        lines.append(f"- `{item.get('status')}` {item.get('agent')}: {item.get('summary')}")
    lines.append("")
    lines.append("## Signals")
    for item in snapshot.get("signals") or []:
        lines.append(f"- {item.get('source')}: {item.get('text')}")
    lines.append("")
    lines.append("## Changed Files")
    for item in snapshot.get("changedFiles") or []:
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def ensure_morpheus_skill(workspace: Workspace, snapshot: dict[str, Any]):
    signals = snapshot.get("signals") or []
    if not signals:
        return None
    name = "morpheus lessons"
    path = workspace.rel("skills", "morpheus", slugify(name), "SKILL.md")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        addition = "\n## Latest Signals\n\n" + "\n".join(
            f"- {item.get('text')}" for item in signals[:5] if isinstance(item, dict)
        ) + "\n"
        if "## Latest Signals" not in text:
            path.write_text(text.rstrip() + "\n" + addition, encoding="utf-8")
        return path
    return create_skill(workspace, name, "Apply recurring lessons detected by the Morpheus self-improvement pass.", "morpheus")


def schedule_exists(workspace: Workspace) -> bool:
    from .scheduler import list_schedules

    return any(str(item.get("name") or "") in {"birkin-morpheus", "birkin-nightly"} for item in list_schedules(workspace))


def summarize_snapshot(snapshot: dict[str, Any], dry_run: bool) -> str:
    mode = "Dry run" if dry_run else "Morpheus"
    return (
        f"{mode} reviewed {len(snapshot.get('runs') or [])} recent runs, "
        f"{len(snapshot.get('signals') or [])} improvement signals, "
        f"{len(snapshot.get('changedFiles') or [])} changed files, and "
        f"{snapshot.get('memory', {}).get('noteCount', 0)} memory notes."
    )


def nightly_config(workspace: Workspace) -> dict[str, Any]:
    return morpheus_config(workspace)


def nightly_status(workspace: Workspace) -> dict[str, Any]:
    return morpheus_status(workspace)


def run_nightly(workspace: Workspace, *, dry_run: bool = False) -> dict[str, Any]:
    return run_morpheus(workspace, dry_run=dry_run)
