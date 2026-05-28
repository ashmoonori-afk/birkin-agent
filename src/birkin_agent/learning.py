from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import json
from typing import Any

from .util import is_relative_to, slugify, utc_stamp, write_json
from .workspace import Workspace


DEFAULT_LEARNING_CONFIG = {
    "eventsPath": "learning/events.jsonl",
    "pendingPath": "learning/proposals/pending",
    "historyPath": "learning/proposals/history",
    "safeConfidence": 0.85,
}

VALID_EVIDENCE_TYPES = {"conversation", "run", "file", "test", "approval", "feedback", "manual"}
STRONG_EVIDENCE_TYPES = {"conversation", "run", "file", "test", "approval", "feedback"}


@dataclass
class LearningProposal:
    id: str
    target_type: str
    target: str
    action: str
    status: str
    risk_tier: str
    confidence: float
    reason: str
    created: str
    payload: dict[str, Any]
    path: Path


def learning_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("learning", {})
    for key, value in DEFAULT_LEARNING_CONFIG.items():
        config.setdefault(key, value)
    return config


def events_path(workspace: Workspace) -> Path:
    path = workspace.rel(str(learning_config(workspace).get("eventsPath") or "learning/events.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def pending_dir(workspace: Workspace) -> Path:
    path = workspace.rel(str(learning_config(workspace).get("pendingPath") or "learning/proposals/pending"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def history_dir(workspace: Workspace) -> Path:
    path = workspace.rel(str(learning_config(workspace).get("historyPath") or "learning/proposals/history"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_evidence(evidence: Any = None, sources: list[str] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    raw_values: list[Any] = []
    if evidence:
        raw_values.extend(evidence if isinstance(evidence, list) else [evidence])
    if sources:
        raw_values.extend(sources)
    for item in raw_values:
        if isinstance(item, dict):
            kind = str(item.get("type") or item.get("kind") or "file").strip().lower()
            ref = str(item.get("ref") or item.get("path") or item.get("source") or "").strip()
            note = str(item.get("note") or "").strip()
        else:
            value = str(item or "").strip()
            if not value:
                continue
            if ":" in value:
                prefix, rest = value.split(":", 1)
                prefix = prefix.strip().lower()
                kind = prefix if prefix in VALID_EVIDENCE_TYPES else "file"
                ref = rest.strip() if prefix in VALID_EVIDENCE_TYPES else value
            elif value == "manual":
                kind = "manual"
                ref = "manual"
            else:
                kind = "file"
                ref = value
            note = ""
        if kind not in VALID_EVIDENCE_TYPES:
            kind = "file"
        if not ref:
            continue
        row = {"type": kind, "ref": ref}
        if note:
            row["note"] = note
        if row not in rows:
            rows.append(row)
    if not rows:
        rows.append({"type": "manual", "ref": "manual"})
    return rows


def evidence_strength(evidence: list[dict[str, str]]) -> float:
    if not evidence:
        return 0.0
    strong = sum(1 for item in evidence if item.get("type") in STRONG_EVIDENCE_TYPES and item.get("ref"))
    manual = sum(1 for item in evidence if item.get("type") == "manual" and item.get("ref"))
    if strong:
        return min(1.0, 0.55 + 0.15 * strong)
    if manual:
        return 0.45
    return 0.25


def high_evidence(workspace: Workspace, confidence: float, evidence: list[dict[str, str]]) -> bool:
    threshold = float(learning_config(workspace).get("safeConfidence") or 0.85)
    return confidence >= threshold and evidence_strength(evidence) >= 0.7


def write_learning_event(
    workspace: Workspace,
    *,
    action: str,
    target_type: str,
    target: str,
    evidence: Any = None,
    confidence: float = 0.7,
    ttl_days: int | None = None,
    scope: dict[str, str] | None = None,
    author: str = "birkin",
    agent: str = "",
    reason: str = "",
    blame: str = "",
    status: str = "applied",
    metadata: dict[str, Any] | None = None,
    rollback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_evidence(evidence)
    event = {
        "id": f"{utc_stamp()}-{slugify(action)}-{slugify(target_type)}-{slugify(target)[:50]}",
        "timestamp": utc_stamp(),
        "action": action,
        "targetType": target_type,
        "target": target,
        "evidence": normalized,
        "evidenceStrength": evidence_strength(normalized),
        "confidence": float(confidence),
        "ttlDays": ttl_days,
        "scope": scope or {},
        "author": author,
        "agent": agent,
        "reason": reason,
        "blame": blame,
        "status": status,
        "metadata": metadata or {},
        "rollback": rollback or {},
    }
    path = events_path(workspace)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_learning_events(workspace: Workspace, limit: int | None = None) -> list[dict[str, Any]]:
    path = events_path(workspace)
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


def learning_event_rows(workspace: Workspace, limit: int = 50) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for event in read_learning_events(workspace, limit=limit):
        rows.append(
            {
                "id": str(event.get("id") or ""),
                "timestamp": str(event.get("timestamp") or ""),
                "status": str(event.get("status") or ""),
                "action": str(event.get("action") or ""),
                "targetType": str(event.get("targetType") or ""),
                "target": str(event.get("target") or ""),
                "confidence": f"{float(event.get('confidence') or 0.0):.3f}",
                "evidenceStrength": f"{float(event.get('evidenceStrength') or 0.0):.3f}",
                "reason": str(event.get("reason") or ""),
            }
        )
    return rows


def diff_text(before: str, after: str, fromfile: str = "before", tofile: str = "after") -> str:
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=fromfile,
            tofile=tofile,
            lineterm="",
        )
    )


def add_learning_proposal(
    workspace: Workspace,
    *,
    target_type: str,
    target: str,
    action: str,
    before: str = "",
    after: str = "",
    evidence: Any = None,
    confidence: float = 0.7,
    ttl_days: int | None = None,
    scope: dict[str, str] | None = None,
    author: str = "birkin",
    agent: str = "",
    reason: str = "",
    blame: str = "",
    risk_tier: str = "review",
    apply_payload: dict[str, Any] | None = None,
) -> LearningProposal:
    normalized = normalize_evidence(evidence)
    proposal_id = f"{utc_stamp()}-{slugify(target_type)}-{slugify(target)[:60]}"
    payload = {
        "id": proposal_id,
        "created": utc_stamp(),
        "status": "pending",
        "targetType": target_type,
        "target": target,
        "action": action,
        "riskTier": risk_tier,
        "confidence": float(confidence),
        "ttlDays": ttl_days,
        "scope": scope or {},
        "author": author,
        "agent": agent,
        "reason": reason,
        "blame": blame,
        "evidence": normalized,
        "evidenceStrength": evidence_strength(normalized),
        "before": before,
        "after": after,
        "diff": diff_text(before, after, target + ":before", target + ":after") if before or after else "",
        "applyPayload": apply_payload or {},
    }
    path = pending_dir(workspace) / f"{proposal_id}.json"
    suffix = 2
    while path.exists():
        payload["id"] = f"{proposal_id}-{suffix}"
        path = pending_dir(workspace) / f"{payload['id']}.json"
        suffix += 1
    write_json(path, payload)
    write_learning_event(
        workspace,
        action="proposal-created",
        target_type=target_type,
        target=target,
        evidence=normalized,
        confidence=confidence,
        ttl_days=ttl_days,
        scope=scope,
        author=author,
        agent=agent,
        reason=reason,
        blame=blame,
        status="pending",
        metadata={"proposalId": payload["id"], "riskTier": risk_tier},
    )
    return proposal_from_payload(path, payload)


def read_proposal(path: Path) -> LearningProposal | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return proposal_from_payload(path, payload) if isinstance(payload, dict) else None


def proposal_from_payload(path: Path, payload: dict[str, Any]) -> LearningProposal:
    return LearningProposal(
        id=str(payload.get("id") or path.stem),
        target_type=str(payload.get("targetType") or ""),
        target=str(payload.get("target") or ""),
        action=str(payload.get("action") or ""),
        status=str(payload.get("status") or "pending"),
        risk_tier=str(payload.get("riskTier") or "review"),
        confidence=float(payload.get("confidence") or 0.0),
        reason=str(payload.get("reason") or ""),
        created=str(payload.get("created") or ""),
        payload=payload,
        path=path,
    )


def list_learning_proposals(workspace: Workspace) -> list[LearningProposal]:
    rows: list[LearningProposal] = []
    for path in sorted(pending_dir(workspace).glob("*.json"), key=lambda item: item.name):
        proposal = read_proposal(path)
        if proposal:
            rows.append(proposal)
    return rows


def learning_proposal_rows(workspace: Workspace) -> list[dict[str, str]]:
    return [
        {
            "id": proposal.id,
            "targetType": proposal.target_type,
            "target": proposal.target,
            "action": proposal.action,
            "status": proposal.status,
            "riskTier": proposal.risk_tier,
            "confidence": f"{proposal.confidence:.3f}",
            "created": proposal.created,
            "reason": proposal.reason,
            "evidence": str(len(proposal.payload.get("evidence") or [])),
        }
        for proposal in list_learning_proposals(workspace)
    ]


def find_learning_proposal(workspace: Workspace, proposal_id: str) -> LearningProposal:
    for proposal in list_learning_proposals(workspace):
        if proposal.id == proposal_id:
            return proposal
    raise KeyError(f"learning proposal not found: {proposal_id}")


def show_learning_proposal(workspace: Workspace, proposal_id: str) -> dict[str, Any]:
    return find_learning_proposal(workspace, proposal_id).payload


def resolve_learning_proposal(
    workspace: Workspace,
    proposal_id: str,
    status: str,
    result: str = "",
) -> dict[str, Any]:
    proposal = find_learning_proposal(workspace, proposal_id)
    payload = dict(proposal.payload)
    payload["status"] = status
    payload["resolved"] = utc_stamp()
    payload["result"] = result
    target = history_dir(workspace) / f"{proposal.id}-{status}.json"
    write_json(target, payload)
    proposal.path.unlink(missing_ok=True)
    write_learning_event(
        workspace,
        action=f"proposal-{status}",
        target_type=proposal.target_type,
        target=proposal.target,
        evidence=payload.get("evidence"),
        confidence=float(payload.get("confidence") or 0.0),
        ttl_days=payload.get("ttlDays") if isinstance(payload.get("ttlDays"), int) else None,
        scope=payload.get("scope") if isinstance(payload.get("scope"), dict) else {},
        author=str(payload.get("author") or "birkin"),
        agent=str(payload.get("agent") or ""),
        reason=str(payload.get("reason") or ""),
        blame=str(payload.get("blame") or ""),
        status=status,
        metadata={"proposalId": proposal.id, "result": result},
    )
    return payload


def approve_learning(workspace: Workspace, proposal_id: str) -> dict[str, Any]:
    proposal = find_learning_proposal(workspace, proposal_id)
    result = apply_learning_payload(workspace, proposal.payload)
    return resolve_learning_proposal(workspace, proposal_id, "approved", result)


def reject_learning(workspace: Workspace, proposal_id: str) -> dict[str, Any]:
    return resolve_learning_proposal(workspace, proposal_id, "rejected", "rejected by user")


def apply_learning_payload(workspace: Workspace, proposal: dict[str, Any]) -> str:
    payload = proposal.get("applyPayload") if isinstance(proposal.get("applyPayload"), dict) else {}
    kind = str(payload.get("kind") or "")
    if kind == "memory-note":
        from .memory import memory_write_note

        note = memory_write_note(
            workspace,
            str(payload.get("title") or proposal.get("target") or ""),
            str(payload.get("body") or proposal.get("after") or ""),
            kind=str(payload.get("memoryKind") or "feedback"),
            note_type=str(payload.get("noteType") or proposal.get("targetType") or "topic"),
            tags=[str(item) for item in payload.get("tags") or []],
            links=[str(item) for item in payload.get("links") or []],
            confidence=float(proposal.get("confidence") or payload.get("confidence") or 0.7),
            sources=[str(item.get("ref") or item) if isinstance(item, dict) else str(item) for item in proposal.get("evidence") or []],
            evidence=proposal.get("evidence"),
            ttl_days=proposal.get("ttlDays") if isinstance(proposal.get("ttlDays"), int) else None,
            scope=payload.get("scope") if isinstance(payload.get("scope"), dict) else proposal.get("scope"),
            author=str(proposal.get("author") or "birkin"),
            agent=str(proposal.get("agent") or ""),
            reason=str(proposal.get("reason") or ""),
            blame=str(proposal.get("blame") or ""),
            append=bool(payload.get("append") or False),
        )
        return f"wrote memory note {note.path.relative_to(workspace.root)}"
    if kind == "file-replace":
        raw_path = str(payload.get("path") or "")
        target = workspace.rel(raw_path)
        if not is_relative_to(target, workspace.root):
            raise ValueError("learning file target must stay inside workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(proposal.get("after") or payload.get("content") or ""), encoding="utf-8")
        return f"wrote {target.relative_to(workspace.root)}"
    return "approved learning proposal; no apply handler registered"


def rollback_learning(workspace: Workspace, event_id: str) -> dict[str, Any]:
    for event in read_learning_events(workspace):
        if str(event.get("id") or "") != event_id:
            continue
        rollback = event.get("rollback") if isinstance(event.get("rollback"), dict) else {}
        kind = str(rollback.get("kind") or "")
        if kind == "file-restore":
            raw_path = str(rollback.get("path") or "")
            target = workspace.rel(raw_path)
            if not is_relative_to(target, workspace.root):
                raise ValueError("rollback file target must stay inside workspace")
            before = str(rollback.get("before") or "")
            if rollback.get("existed") is False:
                target.unlink(missing_ok=True)
                result = f"removed {target.relative_to(workspace.root)}"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(before, encoding="utf-8")
                result = f"restored {target.relative_to(workspace.root)}"
        else:
            result = "no rollback handler registered"
        write_learning_event(
            workspace,
            action="rollback",
            target_type=str(event.get("targetType") or ""),
            target=str(event.get("target") or ""),
            evidence=[{"type": "approval", "ref": event_id}],
            confidence=1.0,
            status="rolled-back",
            reason=f"Rollback of {event_id}",
            metadata={"rolledBackEvent": event_id, "result": result},
        )
        return {"event": event, "result": result}
    raise KeyError(f"learning event not found: {event_id}")
