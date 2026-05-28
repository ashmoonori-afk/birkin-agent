from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import re
from typing import Any

from .util import is_relative_to, slugify, utc_stamp
from .workspace import Workspace


DEFAULT_MEMORY_CONFIG = {
    "provider": "obsidian",
    "vaultPath": "memory/obsidian-vault",
    "allowExternalVault": False,
    "folders": {
        "conversations": "Birkin/Conversations",
        "feedback": "Birkin/Feedback",
        "errors": "Birkin/Errors",
        "runs": "Birkin/Runs",
        "user": "Birkin/User",
        "project": "Birkin/Project",
        "environment": "Birkin/Environment",
        "workflow": "Birkin/Workflow",
        "ephemeral": "Birkin/Ephemeral",
        "negative": "Birkin/Negative",
    },
    "autoCapture": {"chat": True, "runs": True, "feedback": True, "errors": True},
    "historyPath": "memory/history.jsonl",
    "negativeRevalidateDays": 30,
}

VALID_MEMORY_KINDS = {
    "feedback",
    "errors",
    "conversations",
    "runs",
    "user",
    "project",
    "environment",
    "workflow",
    "ephemeral",
    "negative",
    "conversation",
    "run",
    "error",
}
VALID_NOTE_TYPES = {
    "person",
    "project",
    "preference",
    "fact",
    "topic",
    "session",
    "run",
    "error",
    "user",
    "environment",
    "workflow",
    "ephemeral",
    "negative",
    "conversation",
    "feedback",
}
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass
class MemoryNote:
    path: Path
    kind: str
    title: str


def memory_config(workspace: Workspace) -> dict[str, Any]:
    config = workspace.config.setdefault("memory", {})
    for key, value in DEFAULT_MEMORY_CONFIG.items():
        if key not in config:
            config[key] = value.copy() if isinstance(value, dict) else value
    return config


def obsidian_vault_path(workspace: Workspace) -> Path:
    config = memory_config(workspace)
    raw = str(config.get("vaultPath") or "memory/obsidian-vault")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = workspace.rel(raw)
    resolved = path.resolve()
    if not bool(config.get("allowExternalVault") or False) and not is_relative_to(resolved, workspace.root):
        raise ValueError("memory.vaultPath is outside the workspace; set memory.allowExternalVault true to use it")
    return resolved


def memory_status(workspace: Workspace) -> dict[str, Any]:
    config = memory_config(workspace)
    try:
        vault = obsidian_vault_path(workspace)
        error = ""
    except Exception as exc:
        vault = Path(str(config.get("vaultPath") or ""))
        error = str(exc)
    notes = list(vault.rglob("*.md")) if vault.exists() and not error else []
    linked = 0
    for path in notes:
        try:
            if WIKILINK_RE.search(path.read_text(encoding="utf-8", errors="replace")):
                linked += 1
        except OSError:
            continue
    return {
        "provider": str(config.get("provider") or "obsidian"),
        "vaultPath": str(vault),
        "vaultExists": vault.exists() if not error else False,
        "allowExternalVault": bool(config.get("allowExternalVault") or False),
        "noteCount": len(notes),
        "linkedNotes": linked,
        "historyPath": str(memory_history_path(workspace)),
        "types": sorted(VALID_NOTE_TYPES),
        "scopeKeys": ["user", "project", "machine", "channel", "thread", "profile"],
        "error": error,
    }


def validate_memory(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = memory_config(workspace)
    if str(config.get("provider") or "") != "obsidian":
        errors.append(f"unsupported memory provider: {config.get('provider')}")
    try:
        vault = obsidian_vault_path(workspace)
    except Exception as exc:
        errors.append(str(exc))
        return errors, warnings
    if not vault.exists():
        warnings.append(f"Obsidian vault folder will be created on first write: {vault}")
    return errors, warnings


def configure_obsidian_vault(workspace: Workspace, vault_path: str, allow_external: bool = False) -> None:
    config = memory_config(workspace)
    config["provider"] = "obsidian"
    config["vaultPath"] = vault_path
    config["allowExternalVault"] = bool(allow_external)
    obsidian_vault_path(workspace)
    workspace.save_config()


def folder_for_kind(workspace: Workspace, kind: str) -> Path:
    config = memory_config(workspace)
    folders = config.get("folders") if isinstance(config.get("folders"), dict) else {}
    folder = str(folders.get(kind) or folders.get(f"{kind}s") or f"Birkin/{kind.title()}")
    return obsidian_vault_path(workspace) / folder


def normalize_kind(kind: str) -> str:
    value = str(kind or "feedback").strip().lower()
    aliases = {"conversation": "conversations", "run": "runs", "error": "errors"}
    value = aliases.get(value, value)
    return value if value in VALID_MEMORY_KINDS else "feedback"


def normalize_note_type(note_type: str) -> str:
    value = str(note_type or "topic").strip().lower()
    return value if value in VALID_NOTE_TYPES else "topic"


def quote_yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def memory_history_path(workspace: Workspace) -> Path:
    config = memory_config(workspace)
    path = workspace.rel(str(config.get("historyPath") or "memory/history.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_history(workspace: Workspace, payload: dict[str, Any]) -> None:
    payload = {"timestamp": utc_stamp(), **payload}
    with memory_history_path(workspace).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def iso_expiry(ttl_days: int | None) -> str:
    if not ttl_days:
        return ""
    return (datetime.now(timezone.utc) + timedelta(days=max(1, int(ttl_days)))).strftime("%Y%m%dT%H%M%SZ")


def expired(meta: dict[str, Any]) -> bool:
    expires = str(meta.get("expires") or "")
    return bool(expires and expires <= utc_stamp())


def frontmatter(
    *,
    title: str,
    kind: str,
    note_type: str,
    created: str,
    updated: str,
    tags: list[str],
    sources: list[str],
    confidence: float,
    scope: dict[str, str],
    version: int,
    ttl_days: int | None,
    expires: str,
    author: str,
    agent: str,
    reason: str,
    blame: str,
    evidence: list[dict[str, str]],
    revalidate_after: str = "",
) -> str:
    lines = [
        "---",
        f"title: {quote_yaml(title)}",
        f"kind: {kind}",
        f"type: {note_type}",
        f"created: {quote_yaml(created)}",
        f"updated: {quote_yaml(updated)}",
        f"confidence: {float(confidence):.3f}",
        f"version: {int(version)}",
        f"scope: {json.dumps(scope, ensure_ascii=False)}",
        f"sources: {json.dumps(sources, ensure_ascii=False)}",
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
        f"evidence: {json.dumps(evidence, ensure_ascii=False)}",
        f"ttlDays: {int(ttl_days) if ttl_days else 0}",
        f"expires: {quote_yaml(expires)}",
        f"author: {quote_yaml(author)}",
        f"agent: {quote_yaml(agent)}",
        f"reason: {quote_yaml(reason)}",
        f"blame: {quote_yaml(blame)}",
    ]
    if revalidate_after:
        lines.append(f"revalidateAfter: {quote_yaml(revalidate_after)}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    lines = text.splitlines()
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, text
    meta: dict[str, Any] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = parse_frontmatter_value(value.strip())
    return meta, "\n".join(lines[end + 1 :]).strip()


def parse_frontmatter_value(value: str) -> Any:
    if not value:
        return ""
    if value[0] in {'"', "'", "[", "{"}:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.strip("\"'")
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def note_path_for_title(workspace: Workspace, kind: str, title: str, stable: bool) -> Path:
    folder = folder_for_kind(workspace, kind)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{slugify(title)[:80]}.md" if stable else f"{utc_stamp()}-{slugify(title)[:80]}.md"
    return folder / name


def find_note_by_title(workspace: Workspace, title: str, kind: str | None = None) -> Path | None:
    vault = obsidian_vault_path(workspace)
    if not vault.exists():
        return None
    target_slug = slugify(title)
    candidates = [folder_for_kind(workspace, normalize_kind(kind))] if kind else [vault]
    for root in candidates:
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            if path.stem == target_slug or path.stem.endswith("-" + target_slug):
                return path
            try:
                meta, _body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if str(meta.get("title") or "").strip().lower() == title.strip().lower():
                return path
    return None


def write_memory_note(
    workspace: Workspace,
    kind: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    *,
    note_type: str = "topic",
    confidence: float = 0.7,
    sources: list[str] | None = None,
    links: list[str] | None = None,
    append: bool = False,
    stable: bool = False,
    evidence: Any = None,
    ttl_days: int | None = None,
    scope: dict[str, str] | None = None,
    author: str = "birkin",
    agent: str = "",
    reason: str = "",
    blame: str = "",
    expected_version: int | None = None,
    record_learning: bool = True,
) -> MemoryNote:
    kind = normalize_kind(kind)
    note_type = normalize_note_type(note_type)
    tag_values = sorted({*(tags or []), "birkin", kind})
    source_values = [str(item) for item in (sources or []) if str(item).strip()]
    title = title.strip() or kind
    existing = find_note_by_title(workspace, title, kind) if (stable or append) else None
    path = existing or note_path_for_title(workspace, kind, title, stable)
    created = utc_stamp()
    existing_body = ""
    previous_text = ""
    previous_version = 0
    previous_meta: dict[str, Any] = {}
    existed_before = path.exists()
    if existed_before:
        try:
            previous_text = path.read_text(encoding="utf-8", errors="replace")
            meta, existing_body = split_frontmatter(previous_text)
            previous_meta = meta
            created = str(meta.get("created") or created)
            previous_version = int(meta.get("version") or 0)
            if expected_version is not None and previous_version != int(expected_version):
                raise ValueError(f"memory note version mismatch: expected {expected_version}, found {previous_version}")
            old_sources = meta.get("sources")
            if isinstance(old_sources, list):
                source_values = sorted({*source_values, *(str(item) for item in old_sources)})
            old_tags = meta.get("tags")
            if isinstance(old_tags, list):
                tag_values = sorted({*tag_values, *(str(item) for item in old_tags)})
        except OSError:
            pass
    elif expected_version not in {None, 0}:
        raise ValueError(f"memory note version mismatch: expected {expected_version}, found 0")
    body = body.strip()
    if append and existing_body:
        body = existing_body.rstrip() + "\n\n" + body
    body = with_related_links(body, links or [])
    try:
        from .learning import normalize_evidence

        evidence_values = normalize_evidence(evidence, source_values)
    except Exception:
        evidence_values = [{"type": "manual", "ref": "manual"}]
    version = previous_version + 1
    expires = iso_expiry(ttl_days)
    scope_values = {str(key): str(value) for key, value in (scope or {}).items() if str(value).strip()}
    revalidate_after = ""
    if note_type == "negative" or kind == "negative":
        days = ttl_days or int(memory_config(workspace).get("negativeRevalidateDays") or 30)
        revalidate_after = iso_expiry(days)
    content = frontmatter(
        title=title,
        kind=kind,
        note_type=note_type,
        created=created,
        updated=utc_stamp(),
        tags=tag_values,
        sources=source_values,
        confidence=confidence,
        scope=scope_values,
        version=version,
        ttl_days=ttl_days,
        expires=expires,
        author=author,
        agent=agent,
        reason=reason,
        blame=blame,
        evidence=evidence_values,
        revalidate_after=revalidate_after,
    ) + body.rstrip() + "\n"
    path.write_text(content, encoding="utf-8")
    append_history(
        workspace,
        {
            "action": "write",
            "path": str(path.relative_to(workspace.root)) if path.is_relative_to(workspace.root) else str(path),
            "title": title,
            "kind": kind,
            "type": note_type,
            "version": version,
            "previousVersion": previous_version,
            "confidence": confidence,
            "scope": scope_values,
            "ttlDays": ttl_days,
            "evidence": evidence_values,
            "author": author,
            "agent": agent,
            "reason": reason,
            "blame": blame,
        },
    )
    if record_learning:
        try:
            from .learning import write_learning_event

            rel_path = str(path.relative_to(workspace.root)) if path.is_relative_to(workspace.root) else str(path)
            write_learning_event(
                workspace,
                action="memory-write",
                target_type="memory",
                target=title,
                evidence=evidence_values,
                confidence=confidence,
                ttl_days=ttl_days,
                scope=scope_values,
                author=author,
                agent=agent,
                reason=reason,
                blame=blame,
                status="applied",
                metadata={"path": rel_path, "version": version, "kind": kind, "type": note_type},
                rollback={"kind": "file-restore", "path": rel_path, "before": previous_text, "existed": existed_before},
            )
        except Exception:
            pass
    return MemoryNote(path=path, kind=kind, title=title)


def with_related_links(body: str, links: list[str]) -> str:
    clean = [link.strip() for link in links if link and link.strip()]
    if not clean:
        return body
    related = " | ".join(f"[[{link}]]" for link in clean)
    if "## Related" in body:
        return body.rstrip() + "\n" + related
    return body.rstrip() + "\n\n## Related\n" + related


def auto_capture_enabled(workspace: Workspace, key: str) -> bool:
    config = memory_config(workspace)
    auto = config.get("autoCapture")
    if not isinstance(auto, dict):
        return False
    return bool(auto.get(key) or False)


def capture_chat_memory(workspace: Workspace, message: str, reply: str, payload: dict[str, Any]) -> MemoryNote | None:
    if not auto_capture_enabled(workspace, "chat"):
        return None
    title = first_words(message, 8) or "chat"
    body = "\n".join(
        [
            f"# Chat: {title}",
            "",
            f"- Agent: `{payload.get('agent') or ''}`",
            f"- Status: `{payload.get('status') or ''}`",
            f"- Record: `{payload.get('record') or ''}`",
            "",
            "## User",
            "",
            message,
            "",
            "## Assistant",
            "",
            reply,
            "",
        ]
    )
    return write_memory_note(
        workspace,
        "conversations",
        title,
        body,
        ["conversation"],
        note_type="session",
        confidence=0.7,
        sources=[str(payload.get("record") or "chat")],
        evidence=[{"type": "conversation", "ref": str(payload.get("record") or "chat")}],
        scope={"profile": str(payload.get("agent") or "chat")},
        agent=str(payload.get("agent") or "chat"),
        reason="auto-capture chat transcript",
    )


def capture_run_memory(workspace: Workspace, record: Path, payload: dict[str, Any]) -> MemoryNote | None:
    if not auto_capture_enabled(workspace, "runs"):
        return None
    status = str(payload.get("status") or "unknown")
    kind = "errors" if status == "failed" else "runs"
    title = f"{payload.get('agent') or 'agent'} {status}"
    body = "\n".join(
        [
            f"# Run: {title}",
            "",
            f"- Record: `{record}`",
            f"- Status: `{status}`",
            f"- Runner: `{payload.get('runner') or ''}`",
            f"- Model: `{(payload.get('model') or {}).get('id') if isinstance(payload.get('model'), dict) else ''}`",
            "",
            "## Summary",
            "",
            str(payload.get("summary") or ""),
            "",
            "## Task",
            "",
            str(payload.get("task") or ""),
            "",
        ]
    )
    return write_memory_note(
        workspace,
        kind,
        title,
        body,
        ["run", status],
        note_type="error" if status == "failed" else "run",
        confidence=0.8,
        sources=[str(record)],
        evidence=[{"type": "run", "ref": str(record)}],
        scope={"project": workspace.root.name, "profile": str(payload.get("agent") or "agent")},
        agent=str(payload.get("agent") or "agent"),
        reason="auto-capture run summary",
    )


def record_feedback(workspace: Workspace, text: str, kind: str = "feedback") -> MemoryNote:
    kind = normalize_kind(kind)
    title = first_words(text, 8) or kind
    body = f"# {kind.title()}: {title}\n\n{text.strip()}\n"
    return write_memory_note(
        workspace,
        kind,
        title,
        body,
        [kind],
        note_type="fact" if kind == "feedback" else "topic",
        confidence=0.8,
        sources=["manual"],
        evidence=[{"type": "feedback", "ref": "manual"}],
        scope={"profile": "user"},
        author="user",
        reason="manual feedback record",
    )


def memory_write_note(
    workspace: Workspace,
    title: str,
    body: str,
    *,
    kind: str = "feedback",
    note_type: str = "topic",
    tags: list[str] | None = None,
    links: list[str] | None = None,
    confidence: float = 0.7,
    sources: list[str] | None = None,
    append: bool = False,
    evidence: Any = None,
    ttl_days: int | None = None,
    scope: dict[str, str] | None = None,
    author: str = "birkin",
    agent: str = "",
    reason: str = "",
    blame: str = "",
    expected_version: int | None = None,
) -> MemoryNote:
    return write_memory_note(
        workspace,
        kind,
        title,
        body,
        tags,
        note_type=note_type,
        confidence=confidence,
        sources=sources,
        links=links,
        append=append,
        stable=True,
        evidence=evidence,
        ttl_days=ttl_days,
        scope=scope,
        author=author,
        agent=agent,
        reason=reason,
        blame=blame,
        expected_version=expected_version,
    )


def memory_get_note(workspace: Workspace, title: str) -> dict[str, str]:
    path = find_note_by_title(workspace, title)
    if not path:
        raise KeyError(f"memory note not found: {title}")
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = split_frontmatter(text)
    return {
        "title": str(meta.get("title") or title),
        "kind": str(meta.get("kind") or ""),
        "type": str(meta.get("type") or ""),
        "confidence": str(meta.get("confidence") or ""),
        "version": str(meta.get("version") or ""),
        "scope": json.dumps(meta.get("scope") or {}, ensure_ascii=False),
        "ttlDays": str(meta.get("ttlDays") or ""),
        "expires": str(meta.get("expires") or ""),
        "expired": "yes" if expired(meta) else "no",
        "author": str(meta.get("author") or ""),
        "agent": str(meta.get("agent") or ""),
        "reason": str(meta.get("reason") or ""),
        "blame": str(meta.get("blame") or ""),
        "evidence": json.dumps(meta.get("evidence") or [], ensure_ascii=False),
        "path": str(path),
        "body": body,
        "raw": text,
    }


def memory_link(workspace: Workspace, from_title: str, to_title: str) -> MemoryNote:
    note = memory_get_note(workspace, from_title)
    meta, body = split_frontmatter(note["raw"])
    kind = normalize_kind(str(meta.get("kind") or "feedback"))
    note_type = normalize_note_type(str(meta.get("type") or "topic"))
    tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
    sources = meta.get("sources") if isinstance(meta.get("sources"), list) else []
    confidence = float(meta.get("confidence") or 0.7)
    return write_memory_note(
        workspace,
        kind,
        str(meta.get("title") or from_title),
        body,
        [str(item) for item in tags],
        note_type=note_type,
        confidence=confidence,
        sources=[str(item) for item in sources],
        links=[to_title],
        stable=True,
        scope=meta.get("scope") if isinstance(meta.get("scope"), dict) else {},
        ttl_days=int(meta.get("ttlDays") or 0) or None,
        author=str(meta.get("author") or "birkin"),
        agent=str(meta.get("agent") or ""),
        reason=f"link memory note to {to_title}",
        evidence=meta.get("evidence") if isinstance(meta.get("evidence"), list) else sources,
    )


def memory_search(
    workspace: Workspace,
    query: str,
    limit: int = 8,
    *,
    note_type: str | None = None,
    scope: str | None = None,
    min_confidence: float | None = None,
    tag: str | None = None,
    source: str | None = None,
    include_expired: bool = False,
) -> list[dict[str, str]]:
    status = memory_status(workspace)
    if status.get("error") or not status.get("vaultExists"):
        return []
    vault = Path(str(status["vaultPath"]))
    terms = [term for term in re.findall(r"[\w.-]{2,}", query.lower(), flags=re.UNICODE) if term]
    has_filters = any([note_type, scope, min_confidence is not None, tag, source])
    if not terms and not has_filters:
        return []
    matches: list[dict[str, str]] = []
    for path in sorted(vault.rglob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = split_frontmatter(text)
        if expired(meta) and not include_expired:
            continue
        if note_type and str(meta.get("type") or "").lower() != note_type.lower():
            continue
        if min_confidence is not None and float(meta.get("confidence") or 0.0) < float(min_confidence):
            continue
        tags = [str(item) for item in meta.get("tags") or []] if isinstance(meta.get("tags"), list) else []
        if tag and tag not in tags:
            continue
        sources = [str(item) for item in meta.get("sources") or []] if isinstance(meta.get("sources"), list) else []
        evidence = meta.get("evidence") if isinstance(meta.get("evidence"), list) else []
        evidence_refs = [str(item.get("ref") or "") for item in evidence if isinstance(item, dict)]
        if source and not any(source in item for item in [*sources, *evidence_refs]):
            continue
        scope_meta = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
        if scope and not any(scope.lower() in str(value).lower() for value in scope_meta.values()):
            continue
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms) if terms else 1
        links = WIKILINK_RE.findall(text)
        if any(term in " ".join(links).lower() for term in terms):
            score += 2
        if score <= 0:
            continue
        matches.append(
            {
                "path": str(path),
                "title": str(meta.get("title") or path.stem),
                "kind": str(meta.get("kind") or ""),
                "type": str(meta.get("type") or ""),
                "confidence": str(meta.get("confidence") or ""),
                "version": str(meta.get("version") or ""),
                "scope": json.dumps(scope_meta, ensure_ascii=False),
                "expired": "yes" if expired(meta) else "no",
                "score": str(score),
                "snippet": best_snippet(body or text, terms),
            }
        )
        if len(matches) >= limit:
            break
    return matches


def recall_memory(workspace: Workspace, query: str, limit: int = 5) -> list[dict[str, str]]:
    return memory_search(workspace, query, limit=limit)


def best_snippet(text: str, terms: list[str]) -> str:
    for line in text.splitlines():
        lowered = line.lower()
        if any(term in lowered for term in terms):
            return line.strip()[:240]
    return text.strip()[:240]


def first_words(text: str, count: int) -> str:
    words = re.findall(r"[\w.-]+", text, flags=re.UNICODE)
    return " ".join(words[:count])
