from __future__ import annotations

from datetime import datetime
import json
import subprocess
from typing import Any

from .approvals import propose_action
from .improve import collect_signals
from .learning import add_learning_proposal, high_evidence, normalize_evidence
from .ledger import ledger_rows, ledger_summary
from .memory import memory_search, memory_status, memory_write_note
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
        evidence = morpheus_evidence(snapshot)
        confidence = morpheus_confidence(snapshot)
        body = render_morpheus_memory(snapshot)
        title = f"Morpheus self-improvement {datetime.now().strftime('%Y-%m-%d')}"
        if high_evidence(workspace, confidence, evidence):
            note = memory_write_note(
                workspace,
                title,
                body,
                kind="runs",
                note_type="workflow",
                tags=["morpheus", "self-improvement"],
                links=["Birkin Ledger", "Birkin Skills"],
                confidence=confidence,
                sources=[item["ref"] for item in evidence],
                evidence=evidence,
                scope={"project": workspace.root.name, "profile": "morpheus"},
                agent="morpheus",
                reason="high-evidence Morpheus review",
                append=True,
            )
            actions.append({"type": "memory", "path": str(note.path), "evidence": len(evidence), "confidence": confidence})
        else:
            proposal = add_learning_proposal(
                workspace,
                target_type="memory",
                target=title,
                action="morpheus-memory-write",
                before="",
                after=body,
                evidence=evidence,
                confidence=confidence,
                scope={"project": workspace.root.name, "profile": "morpheus"},
                agent="morpheus",
                reason="Morpheus evidence below safe apply threshold",
                risk_tier="review",
                apply_payload={
                    "kind": "memory-note",
                    "title": title,
                    "body": body,
                    "memoryKind": "runs",
                    "noteType": "workflow",
                    "tags": ["morpheus", "self-improvement"],
                    "links": ["Birkin Ledger", "Birkin Skills"],
                    "append": True,
                    "scope": {"project": workspace.root.name, "profile": "morpheus"},
                },
            )
            actions.append({"type": "learning-proposal", "id": proposal.id, "target": proposal.target})
        skill_proposal = ensure_morpheus_skill(workspace, snapshot)
        if skill_proposal:
            actions.append(skill_proposal)
        if not schedule_exists(workspace):
            proposal = propose_action(
                workspace,
                category="schedule",
                title="Daily Birkin Morpheus self-improvement at 04:00",
                description="Enable the portable daemon to run the Morpheus review at 04:00.",
                payload={"name": "birkin-morpheus", "hour": 4, "minute": 0, "action": "morpheus", "payload": {"dryRun": True}},
                origin="morpheus",
                evidence=evidence,
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
    try:
        from .reliability import log_reliability_event

        log_reliability_event(
            workspace,
            stage="agent",
            status=result["status"],
            trace_id=path.stem,
            resource="morpheus",
            message=result["summary"],
            evidence=morpheus_evidence(snapshot),
            metadata={"actions": actions},
        )
    except Exception:
        pass
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
    signals = signal_rows(collect_signals(workspace)[:20])
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
        if isinstance(item, dict):
            lines.append(f"- {item.get('source')}: {item.get('text')}")
        else:
            lines.append(f"- {item}")
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
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    if before:
        header = ""
    else:
        header = f"""---
name: {slugify(name)}
description: Apply recurring lessons detected by the Morpheus self-improvement pass.
version: 0.1.0
permissions: {{"tools": [], "resources": ["workspace"], "approval": "review"}}
metadata: {{"birkin": {{"author": "morpheus", "source": "generated-proposal", "tests": ["birkin-codex skills validate"], "lastVerified": "", "immutable": false}}, "openclaw": {{"alwaysInclude": true}}}}
---

# {name}
"""
    addition = "\n## Latest Signals\n\n" + "\n".join(
        f"- {item.get('text')}" for item in signals[:5] if isinstance(item, dict)
    ) + "\n"
    after = (before.rstrip() if before else header.rstrip()) + "\n\n" + addition
    proposal = add_learning_proposal(
        workspace,
        target_type="skill",
        target=name,
        action="morpheus-skill-update",
        before=before,
        after=after,
        evidence=morpheus_evidence(snapshot),
        confidence=morpheus_confidence(snapshot),
        scope={"project": workspace.root.name, "profile": "morpheus"},
        agent="morpheus",
        reason="Morpheus skill updates require proposal approval",
        risk_tier="review",
        apply_payload={"kind": "file-replace", "path": str(path.relative_to(workspace.root)), "content": after},
    )
    return {"type": "learning-proposal", "id": proposal.id, "target": proposal.target}


def signal_rows(signals: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for signal in signals:
        source, text = signal.split(":", 1) if ":" in signal else ("memory/lessons.md", signal)
        rows.append({"source": source.strip(), "text": text.strip()})
    return rows


def morpheus_evidence(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for run in snapshot.get("runs") or []:
        if isinstance(run, dict) and run.get("record"):
            rows.append({"type": "run", "ref": str(run["record"])})
    for signal in snapshot.get("signals") or []:
        if isinstance(signal, dict):
            rows.append({"type": "feedback", "ref": str(signal.get("source") or "memory/lessons.md"), "note": str(signal.get("text") or "")[:160]})
    for changed in snapshot.get("changedFiles") or []:
        rows.append({"type": "file", "ref": str(changed)})
    return normalize_evidence(rows or [{"type": "run", "ref": "morpheus"}])


def morpheus_confidence(snapshot: dict[str, Any]) -> float:
    signals = len(snapshot.get("signals") or [])
    runs = len(snapshot.get("runs") or [])
    changed = len(snapshot.get("changedFiles") or [])
    score = 0.55 + min(0.2, signals * 0.03) + min(0.1, runs * 0.01) + min(0.05, changed * 0.01)
    return min(0.92, score)


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
