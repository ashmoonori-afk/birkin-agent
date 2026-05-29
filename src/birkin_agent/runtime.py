from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .api import endpoint_url, resolve_api_profile
from .approvals import propose_action
from .memory import find_note_by_title, memory_get_note, memory_link, memory_search, memory_write_note
from .skills import discover_skills, parse_frontmatter, render_skill_content
from .util import is_relative_to
from .workspace import Workspace


MAX_FILE_READ_BYTES = 200_000
MAX_TOOL_OUTPUT_CHARS = 30_000


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


@dataclass
class RuntimeTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], ToolResult]

    def openai_spec(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RuntimeTool] = {}

    def register(self, tool: RuntimeTool) -> None:
        self._tools[tool.name] = tool

    def specs(self) -> list[dict[str, Any]]:
        return [tool.openai_spec() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(f"unknown tool: {name}", is_error=True)
        try:
            return tool.handler(arguments)
        except Exception as exc:
            return ToolResult(f"{type(exc).__name__}: {exc}", is_error=True)


def run_tool_agent(
    workspace: Workspace,
    *,
    packet: dict[str, Any],
    api_profile: str,
    model: str,
    timeout_seconds: int = 1800,
    max_turns: int = 8,
) -> dict[str, Any]:
    profile = resolve_api_profile(workspace, api_profile)
    if profile.type != "openai-compatible":
        raise ValueError(f"{profile.id}: unsupported api profile type: {profile.type}")

    registry = build_registry(workspace, packet)
    system = "\n".join(
        [
            "You are Birkin Codex, a local workspace agent.",
            "Use tools only when they are needed. Consequential actions return approval IDs instead of executing directly.",
            "Prefer memory_search before relying on uncertain prior context.",
            "Return a concise final answer when no more tools are needed.",
        ]
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": str(packet.get("prompt") or packet.get("task") or "")},
    ]
    tool_calls: list[dict[str, Any]] = []
    usage: dict[str, int] = {}
    final_text = ""

    for _turn in range(max(1, max_turns)):
        response = call_openai_tool_turn(
            workspace,
            profile_id=api_profile,
            model=model,
            messages=messages,
            tools=registry.specs(),
            timeout_seconds=timeout_seconds,
        )
        usage = merge_usage(usage, response.get("usage") if isinstance(response.get("usage"), dict) else {})
        message = extract_message(response)
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            final_text = content.strip()
        calls = message.get("tool_calls")
        if not isinstance(calls, list) or not calls:
            return {
                "returncode": 0,
                "stdout": final_text,
                "stderr": "",
                "apiProfile": api_profile,
                "model": model,
                "usage": usage,
                "toolCalls": tool_calls,
                "response": response,
            }

        messages.append(normalize_assistant_message(message))
        for call in calls:
            call_id = str(call.get("id") or f"call_{len(tool_calls) + 1}")
            function = call.get("function") if isinstance(call.get("function"), dict) else {}
            name = str(function.get("name") or "")
            arguments = parse_tool_arguments(function.get("arguments"))
            result = registry.execute(name, arguments)
            tool_calls.append(
                {
                    "id": call_id,
                    "name": name,
                    "arguments": arguments,
                    "isError": result.is_error,
                    "content": result.content[:2000],
                }
            )
            messages.append({"role": "tool", "tool_call_id": call_id, "content": result.content})

    final_text = final_text or "Stopped after the configured tool-call turn limit."
    return {
        "returncode": 2,
        "stdout": final_text,
        "stderr": "tool turn limit reached",
        "apiProfile": api_profile,
        "model": model,
        "usage": usage,
        "toolCalls": tool_calls,
    }


def call_openai_tool_turn(
    workspace: Workspace,
    *,
    profile_id: str,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    timeout_seconds: int,
) -> dict[str, Any]:
    profile = resolve_api_profile(workspace, profile_id)
    payload = {"model": model, "messages": messages, "tools": tools, "stream": False}
    data = json.dumps(payload).encode("utf-8")
    headers = {"content-type": "application/json"}
    if profile.api_key_env:
        import os

        api_key = os.getenv(profile.api_key_env)
        if not api_key:
            raise ValueError(f"{profile.id}: environment variable not set: {profile.api_key_env}")
        headers["authorization"] = f"Bearer {api_key}"
    request = Request(endpoint_url(profile), data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            if not isinstance(parsed, dict):
                raise ValueError("API response must be a JSON object")
            return parsed
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:2000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"API request failed: {exc.reason}") from exc
    except OSError as exc:
        raise RuntimeError(f"API request failed: {exc}") from exc


def extract_message(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict) and isinstance(first.get("message"), dict):
            return first["message"]
    return {"role": "assistant", "content": json.dumps(response, ensure_ascii=False)}


def normalize_assistant_message(message: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "role": "assistant",
        "content": message.get("content") if message.get("content") is not None else "",
    }
    calls = message.get("tool_calls")
    if isinstance(calls, list):
        normalized["tool_calls"] = calls
    return normalized


def parse_tool_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def merge_usage(current: dict[str, int], incoming: dict[str, Any]) -> dict[str, int]:
    merged = dict(current)
    for key, value in incoming.items():
        if isinstance(value, int):
            merged[key] = int(merged.get(key, 0)) + value
    return merged


def build_registry(workspace: Workspace, packet: dict[str, Any]) -> ToolRegistry:
    registry = ToolRegistry()

    def add(name: str, description: str, parameters: dict[str, Any], handler: Callable[[dict[str, Any]], ToolResult]) -> None:
        registry.register(RuntimeTool(name, description, parameters, handler))

    add(
        "load_skill",
        "Load one eligible SKILL.md body by skill name.",
        object_schema({"name": {"type": "string"}}, required=["name"]),
        lambda args: load_skill_tool(workspace, str(args.get("name") or "")),
    )
    add(
        "create_skill",
        "Create a safe workspace skill stub. Use only for reusable procedures.",
        object_schema(
            {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "group": {"type": "string", "default": "custom"},
            },
            required=["name", "description"],
        ),
        lambda args: create_skill_tool(workspace, args),
    )
    add(
        "memory_write_note",
        "Write or append a semantic Obsidian memory note with frontmatter and wikilinks.",
        object_schema(
            {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "kind": {
                    "type": "string",
                    "enum": [
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
                    ],
                },
                "type": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "sources": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "array", "items": {"type": "object"}},
                "links": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
                "ttlDays": {"type": "integer"},
                "scope": {"type": "object"},
                "reason": {"type": "string"},
                "expectedVersion": {"type": "integer"},
                "append": {"type": "boolean"},
            },
            required=["title", "body"],
        ),
        lambda args: memory_write_tool(workspace, args),
    )
    add(
        "memory_search",
        "Search Obsidian memory notes by keyword and wikilink.",
        object_schema({"query": {"type": "string"}, "limit": {"type": "integer"}}, required=["query"]),
        lambda args: json_result(memory_search(workspace, str(args.get("query") or ""), int(args.get("limit") or 8))),
    )
    add(
        "memory_get_note",
        "Read one memory note by title.",
        object_schema({"title": {"type": "string"}}, required=["title"]),
        lambda args: json_result(memory_get_note(workspace, str(args.get("title") or ""))),
    )
    add(
        "memory_link",
        "Add a wikilink from one memory note to another.",
        object_schema({"from_title": {"type": "string"}, "to_title": {"type": "string"}}, required=["from_title", "to_title"]),
        lambda args: link_tool(workspace, args),
    )
    add(
        "read_file",
        "Read a UTF-8 text file inside the workspace. Large files are truncated.",
        object_schema({"path": {"type": "string"}}, required=["path"]),
        lambda args: read_file_tool(workspace, str(args.get("path") or "")),
    )
    add(
        "list_files",
        "List files under a workspace path.",
        object_schema({"path": {"type": "string"}, "depth": {"type": "integer"}}, required=[]),
        lambda args: list_files_tool(workspace, str(args.get("path") or "."), int(args.get("depth") or 1)),
    )
    add(
        "write_file",
        "Queue approval to create or overwrite a workspace text file.",
        object_schema({"path": {"type": "string"}, "content": {"type": "string"}}, required=["path", "content"]),
        lambda args: queue_file_write_tool(workspace, args),
    )
    add(
        "run_shell",
        "Queue approval to run a shell command inside the workspace.",
        object_schema(
            {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout": {"type": "integer"},
            },
            required=["command"],
        ),
        lambda args: queue_approval_tool(
            workspace,
            "shell",
            "Shell command",
            str(args.get("command") or ""),
            {"command": str(args.get("command") or ""), "cwd": str(args.get("cwd") or "."), "timeout": int(args.get("timeout") or 120)},
        ),
    )
    add(
        "web_fetch",
        "Queue approval to fetch an external URL. External calls are consequential when requested by the model.",
        object_schema({"url": {"type": "string"}}, required=["url"]),
        lambda args: queue_approval_tool(workspace, "external", "External web fetch", str(args.get("url") or ""), {"url": str(args.get("url") or "")}),
    )
    add(
        "spawn_subagent",
        "Run a scoped packet-only subagent and return its run record path.",
        object_schema({"agent": {"type": "string"}, "task": {"type": "string"}}, required=["agent", "task"]),
        lambda args: subagent_tool(workspace, args),
    )
    add(
        "schedule_daily",
        "Queue approval for a daily schedule or cron-like local automation.",
        object_schema(
            {
                "name": {"type": "string"},
                "hour": {"type": "integer"},
                "minute": {"type": "integer"},
                "action": {"type": "string"},
                "payload": {"type": "object"},
            },
            required=["name", "hour"],
        ),
        lambda args: queue_approval_tool(workspace, "schedule", str(args.get("name") or "Daily schedule"), "Daily schedule proposal", args),
    )
    add(
        "telegram_send",
        "Queue approval to send a Telegram message.",
        object_schema({"message": {"type": "string"}}, required=["message"]),
        lambda args: queue_approval_tool(workspace, "telegram", "Telegram message", str(args.get("message") or ""), {"message": str(args.get("message") or "")}),
    )
    return registry


def object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required}


def json_result(value: Any) -> ToolResult:
    return ToolResult(json.dumps(value, ensure_ascii=False, indent=2)[:MAX_TOOL_OUTPUT_CHARS])


def load_skill_tool(workspace: Workspace, name: str) -> ToolResult:
    for skill in discover_skills(workspace):
        if skill.name == name and skill.enabled and skill.eligible:
            _frontmatter, body, issues = parse_frontmatter(skill.path)
            if issues:
                return ToolResult("; ".join(issues), is_error=True)
            text = body.strip()
            if len(text) > MAX_TOOL_OUTPUT_CHARS:
                text = text[:MAX_TOOL_OUTPUT_CHARS] + "\n[truncated]"
            return ToolResult(text)
    return ToolResult(f"skill not found or not eligible: {name}", is_error=True)


def create_skill_tool(workspace: Workspace, args: dict[str, Any]) -> ToolResult:
    from .learning import add_learning_proposal
    from .util import slugify

    name = str(args.get("name") or "")
    description = str(args.get("description") or "")
    group = str(args.get("group") or "custom")
    rel_path = Path("skills") / slugify(group) / slugify(name) / "SKILL.md"
    path = workspace.rel(str(rel_path))
    before = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    after = render_skill_content(name, description)
    proposal = add_learning_proposal(
        workspace,
        target_type="skill",
        target=name,
        action="skill-create",
        before=before,
        after=after,
        evidence=[{"type": "run", "ref": "tool-agent"}],
        confidence=0.8,
        agent="tool-agent",
        reason="tool-agent proposed skill creation",
        risk_tier="review",
        apply_payload={"kind": "file-replace", "path": str(rel_path), "content": after},
    )
    return ToolResult(f"queued learning proposal {proposal.id} for skill {path.relative_to(workspace.root)}")


def memory_write_tool(workspace: Workspace, args: dict[str, Any]) -> ToolResult:
    title = str(args.get("title") or "")
    body = str(args.get("body") or "")
    kind = str(args.get("kind") or "feedback")
    append = bool(args.get("append") or False)
    expected_version = int(args.get("expectedVersion") or 0) or None
    existing = find_note_by_title(workspace, title, kind)
    if existing and not append and expected_version is None:
        from .learning import add_learning_proposal

        before = existing.read_text(encoding="utf-8", errors="replace")
        proposal = add_learning_proposal(
            workspace,
            target_type="memory",
            target=title,
            action="memory-write",
            before=before,
            after=body,
            evidence=args.get("evidence") if isinstance(args.get("evidence"), list) else args.get("sources"),
            confidence=float(args.get("confidence") or 0.7),
            ttl_days=int(args.get("ttlDays") or 0) or None,
            scope=args.get("scope") if isinstance(args.get("scope"), dict) else {},
            agent="tool-agent",
            reason=str(args.get("reason") or "tool-agent proposed memory overwrite"),
            risk_tier="review",
            apply_payload={
                "kind": "memory-note",
                "title": title,
                "body": body,
                "memoryKind": kind,
                "noteType": str(args.get("type") or "topic"),
                "tags": [str(item) for item in args.get("tags") or []],
                "links": [str(item) for item in args.get("links") or []],
                "append": False,
                "scope": args.get("scope") if isinstance(args.get("scope"), dict) else {},
            },
        )
        return ToolResult(f"queued learning proposal {proposal.id} for existing memory note")
    note = memory_write_note(
        workspace,
        title,
        body,
        kind=kind,
        note_type=str(args.get("type") or "topic"),
        tags=[str(item) for item in args.get("tags") or []],
        links=[str(item) for item in args.get("links") or []],
        confidence=float(args.get("confidence") or 0.7),
        sources=[str(item) for item in args.get("sources") or []],
        evidence=args.get("evidence") if isinstance(args.get("evidence"), list) else None,
        ttl_days=int(args.get("ttlDays") or 0) or None,
        scope=args.get("scope") if isinstance(args.get("scope"), dict) else {},
        agent="tool-agent",
        reason=str(args.get("reason") or "tool-agent memory write"),
        expected_version=expected_version,
        append=append,
    )
    return ToolResult(f"wrote {note.path.relative_to(workspace.root)}")


def link_tool(workspace: Workspace, args: dict[str, Any]) -> ToolResult:
    note = memory_link(workspace, str(args.get("from_title") or ""), str(args.get("to_title") or ""))
    return ToolResult(f"linked {note.title} -> {args.get('to_title')}")


def workspace_path(workspace: Workspace, raw: str) -> Path:
    path = Path(raw).expanduser()
    resolved = path.resolve() if path.is_absolute() else workspace.rel(raw)
    if not is_relative_to(resolved, workspace.root):
        raise ValueError(f"path escapes workspace: {raw}")
    return resolved


def read_file_tool(workspace: Workspace, raw_path: str) -> ToolResult:
    path = workspace_path(workspace, raw_path)
    if not path.is_file():
        return ToolResult(f"not a file: {raw_path}", is_error=True)
    data = path.read_bytes()
    truncated = len(data) > MAX_FILE_READ_BYTES
    text = data[:MAX_FILE_READ_BYTES].decode("utf-8", errors="replace")
    if truncated:
        text += f"\n[truncated; file is {len(data)} bytes]"
    return ToolResult(text)


def list_files_tool(workspace: Workspace, raw_path: str, depth: int) -> ToolResult:
    base = workspace_path(workspace, raw_path or ".")
    if not base.exists():
        return ToolResult(f"path does not exist: {raw_path}", is_error=True)
    if base.is_file():
        return ToolResult(str(base.relative_to(workspace.root)))
    skip = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}
    lines: list[str] = []

    def walk(path: Path, level: int) -> None:
        if level > depth:
            return
        for child in sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
            if child.name in skip:
                continue
            rel = child.relative_to(workspace.root)
            lines.append(("  " * (level - 1)) + str(rel) + ("/" if child.is_dir() else ""))
            if child.is_dir():
                walk(child, level + 1)

    walk(base, 1)
    return ToolResult("\n".join(lines[:500]) or "(empty)")


def queue_file_write_tool(workspace: Workspace, args: dict[str, Any]) -> ToolResult:
    rel_path = str(args.get("path") or "")
    workspace_path(workspace, rel_path)
    return queue_approval_tool(
        workspace,
        "file",
        f"Write {rel_path}",
        f"Create or overwrite {rel_path}",
        {"path": rel_path, "content": str(args.get("content") or "")},
    )


def queue_approval_tool(
    workspace: Workspace,
    category: str,
    title: str,
    description: str,
    payload: dict[str, Any],
) -> ToolResult:
    status = propose_action(
        workspace,
        category=category,
        title=title,
        description=description,
        payload=payload,
        origin="tool-agent",
        evidence=[{"type": "run", "ref": str(payload.get("record") or "tool-agent")}],
    )
    if status.get("status") == "pending":
        return ToolResult(f"queued approval {status.get('id')}")
    return ToolResult(json.dumps(status, ensure_ascii=False))


def subagent_tool(workspace: Workspace, args: dict[str, Any]) -> ToolResult:
    from .agents import run_agent

    agent_id = str(args.get("agent") or "")
    task = str(args.get("task") or "")
    record, result = run_agent(workspace, agent_id, task, execute=False)
    payload = {"record": str(record), "result": result}
    return json_result(payload)
