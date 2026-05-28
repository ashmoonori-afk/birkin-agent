from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    },
    "autoCapture": {"chat": True, "runs": True, "feedback": True, "errors": True},
}


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
    return {
        "provider": str(config.get("provider") or "obsidian"),
        "vaultPath": str(vault),
        "vaultExists": vault.exists() if not error else False,
        "allowExternalVault": bool(config.get("allowExternalVault") or False),
        "noteCount": len(notes),
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


def frontmatter(title: str, kind: str, tags: list[str]) -> str:
    tag_text = ", ".join(tags)
    return "\n".join(
        [
            "---",
            f'title: "{title.replace(chr(34), chr(39))}"',
            f"kind: {kind}",
            f"created: {utc_stamp()}",
            f"tags: [{tag_text}]",
            "---",
            "",
        ]
    )


def write_memory_note(
    workspace: Workspace,
    kind: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
) -> MemoryNote:
    folder = folder_for_kind(workspace, kind)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{utc_stamp()}-{slugify(title)[:80]}.md"
    path = folder / filename
    tag_values = tags or ["birkin", kind]
    content = frontmatter(title, kind, tag_values) + body.rstrip() + "\n"
    path.write_text(content, encoding="utf-8")
    return MemoryNote(path=path, kind=kind, title=title)


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
    return write_memory_note(workspace, "conversations", title, body, ["birkin", "conversation"])


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
    return write_memory_note(workspace, kind, title, body, ["birkin", "run", status])


def record_feedback(workspace: Workspace, text: str, kind: str = "feedback") -> MemoryNote:
    if kind not in {"feedback", "errors", "conversations", "runs"}:
        raise ValueError("memory kind must be feedback, errors, conversations, or runs")
    title = first_words(text, 8) or kind
    body = f"# {kind.title()}: {title}\n\n{text.strip()}\n"
    return write_memory_note(workspace, kind, title, body, ["birkin", kind])


def recall_memory(workspace: Workspace, query: str, limit: int = 5) -> list[dict[str, str]]:
    status = memory_status(workspace)
    if status.get("error") or not status.get("vaultExists"):
        return []
    vault = Path(str(status["vaultPath"]))
    terms = [term for term in re.findall(r"[A-Za-z0-9가-힣_-]{3,}", query.lower()) if term]
    if not terms:
        return []
    matches: list[dict[str, str]] = []
    for path in sorted(vault.rglob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if score <= 0:
            continue
        snippet = best_snippet(text, terms)
        matches.append(
            {
                "path": str(path),
                "title": path.stem,
                "score": str(score),
                "snippet": snippet,
            }
        )
        if len(matches) >= limit:
            break
    return matches


def best_snippet(text: str, terms: list[str]) -> str:
    for line in text.splitlines():
        lowered = line.lower()
        if any(term in lowered for term in terms):
            return line.strip()[:240]
    return text.strip()[:240]


def first_words(text: str, count: int) -> str:
    words = re.findall(r"[A-Za-z0-9가-힣_-]+", text)
    return " ".join(words[:count])
