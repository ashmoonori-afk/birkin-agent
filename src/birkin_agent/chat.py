from __future__ import annotations

import json
from typing import Any

from .agents import list_agents, run_agent
from .memory import capture_chat_memory, recall_memory
from .workspace import Workspace


def default_chat_agent(workspace: Workspace) -> str:
    agent_ids = [agent.id for agent in list_agents(workspace)]
    if "chat" in agent_ids:
        return "chat"
    if agent_ids:
        return agent_ids[0]
    raise KeyError("no agents configured")


def chat_task(
    message: str,
    history: list[dict[str, str]] | None = None,
    recalled: list[dict[str, str]] | None = None,
) -> str:
    parts = ["## Chat Mode", "Answer the user's latest message using the workspace context and available skills."]
    if recalled:
        parts.append("## Recalled Memory")
        for item in recalled:
            parts.append(
                f"- {item.get('title') or ''}: {item.get('snippet') or ''} ({item.get('path') or ''})"
            )
    clean_history = normalize_history(history or [])
    if clean_history:
        parts.append("## Recent Conversation")
        for item in clean_history[-12:]:
            role = item["role"]
            content = item["content"]
            parts.append(f"{role}: {content}")
    parts.append("## User Message")
    parts.append(message)
    return "\n\n".join(parts)


def normalize_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content[:4000]})
    return normalized


def run_chat(
    workspace: Workspace,
    message: str,
    agent_id: str | None = None,
    model_name: str | None = None,
    provider_name: str | None = None,
    execute: bool = False,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    clean_message = message.strip()
    if not clean_message:
        raise ValueError("message is required")
    selected_agent = agent_id or default_chat_agent(workspace)
    recalled = recall_memory(workspace, clean_message)
    task = chat_task(clean_message, history, recalled)
    record, result = run_agent(
        workspace,
        selected_agent,
        task,
        model_name=model_name,
        provider_name=provider_name,
        execute=execute,
    )
    payload = json.loads(record.read_text(encoding="utf-8"))
    reply = str(result.get("stdout") or "").strip()
    if not reply:
        reply = str(payload.get("summary") or "Prompt packet built; runner was not executed.")
    chat_payload = {
        "record": str(record),
        "agent": selected_agent,
        "model": payload.get("model") or {},
        "status": payload.get("status") or "unknown",
        "reply": reply,
        "result": result,
        "usage": payload.get("usage") or {},
        "memory": recalled,
    }
    try:
        note = capture_chat_memory(workspace, clean_message, reply, chat_payload)
        if note:
            chat_payload["memoryNote"] = str(note.path)
    except Exception as exc:
        chat_payload["memoryError"] = str(exc)
    return chat_payload
