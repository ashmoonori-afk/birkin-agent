from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .workspace import Workspace


def ledger_path(workspace: Workspace) -> Path:
    return workspace.rel("usage", "ledger.jsonl")


def provider_usage(result: dict[str, Any]) -> dict[str, int]:
    response = result.get("response") if isinstance(result.get("response"), dict) else {}
    raw_usage = response.get("usage") if isinstance(response.get("usage"), dict) else result.get("usage")
    if not isinstance(raw_usage, dict):
        return {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0}
    prompt = int(raw_usage.get("prompt_tokens") or raw_usage.get("input_tokens") or raw_usage.get("promptTokens") or 0)
    completion = int(
        raw_usage.get("completion_tokens")
        or raw_usage.get("output_tokens")
        or raw_usage.get("completionTokens")
        or 0
    )
    total = int(raw_usage.get("total_tokens") or raw_usage.get("totalTokens") or prompt + completion)
    return {"promptTokens": prompt, "completionTokens": completion, "totalTokens": total}


def append_ledger_entry(workspace: Workspace, record: Path, payload: dict[str, Any]) -> None:
    path = ledger_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    model = payload.get("model") if isinstance(payload.get("model"), dict) else {}
    provider = provider_usage(result)
    entry = {
        "timestamp": payload.get("timestamp") or "",
        "runId": record.stem,
        "record": str(record.relative_to(workspace.root)) if record.is_relative_to(workspace.root) else str(record),
        "agent": payload.get("agent") or "",
        "runner": payload.get("runner") or "",
        "status": payload.get("status") or "",
        "modelId": model.get("id") or "",
        "provider": model.get("provider") or "",
        "model": model.get("model") or "",
        "estimatedTokens": int(usage.get("estimatedTokens") or 0),
        "promptChars": int(usage.get("promptChars") or 0),
        "stdoutChars": int(usage.get("stdoutChars") or 0),
        "stderrChars": int(usage.get("stderrChars") or 0),
        "providerPromptTokens": provider["promptTokens"],
        "providerCompletionTokens": provider["completionTokens"],
        "providerTotalTokens": provider["totalTokens"],
        "costUsd": 0.0,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_ledger(workspace: Workspace, limit: int | None = None) -> list[dict[str, Any]]:
    path = ledger_path(workspace)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    rows = list(reversed(rows))
    return rows[:limit] if limit else rows


def ledger_summary(workspace: Workspace) -> dict[str, Any]:
    rows = read_ledger(workspace)
    status_counts: dict[str, int] = {}
    totals = {
        "runs": len(rows),
        "estimatedTokens": 0,
        "providerPromptTokens": 0,
        "providerCompletionTokens": 0,
        "providerTotalTokens": 0,
        "costUsd": 0.0,
    }
    for row in rows:
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        totals["estimatedTokens"] += int(row.get("estimatedTokens") or 0)
        totals["providerPromptTokens"] += int(row.get("providerPromptTokens") or 0)
        totals["providerCompletionTokens"] += int(row.get("providerCompletionTokens") or 0)
        totals["providerTotalTokens"] += int(row.get("providerTotalTokens") or 0)
        totals["costUsd"] += float(row.get("costUsd") or 0.0)
    return {"path": str(ledger_path(workspace)), "totals": totals, "statusCounts": status_counts}


def ledger_rows(workspace: Workspace, limit: int = 50) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_ledger(workspace, limit=limit):
        rows.append(
            {
                "timestamp": str(row.get("timestamp") or ""),
                "runId": str(row.get("runId") or ""),
                "agent": str(row.get("agent") or ""),
                "status": str(row.get("status") or ""),
                "model": str(row.get("modelId") or row.get("model") or ""),
                "estimatedTokens": str(row.get("estimatedTokens") or 0),
                "providerTokens": str(row.get("providerTotalTokens") or 0),
                "costUsd": f"{float(row.get('costUsd') or 0.0):.6f}",
            }
        )
    return rows
