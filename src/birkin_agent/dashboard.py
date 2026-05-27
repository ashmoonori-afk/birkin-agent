from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agents import agent_rows, validate_agents
from .api import api_rows, validate_api
from .auth import auth_rows, validate_auth
from .gateway import gateway_info, validate_gateway
from .improve import collect_signals
from .models import model_rows, validate_models
from .skills import discover_skills, skill_config_rows, skill_rows, validate_skills
from .workspace import Workspace


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def packet_usage(packet: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, int]:
    result = result or {}
    prompt = str(packet.get("prompt") or "")
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    return {
        "promptChars": len(prompt),
        "promptWords": len(prompt.split()),
        "estimatedTokens": estimate_tokens(prompt),
        "skills": len(packet.get("skills") or []),
        "stdoutChars": len(stdout),
        "stderrChars": len(stderr),
    }


def result_summary(status: str, packet: dict[str, Any], result: dict[str, Any]) -> str:
    if status == "running":
        return "Job is still marked running."
    if status == "packet-only":
        return f"Prompt packet built with {len(packet.get('skills') or [])} skills; no model runner executed."
    if status == "ok":
        stdout = str(result.get("stdout") or "").strip()
        return first_line(stdout) or "Runner finished successfully."
    if status == "failed":
        stderr = str(result.get("stderr") or "").strip()
        stdout = str(result.get("stdout") or "").strip()
        return first_line(stderr) or first_line(stdout) or "Runner failed without output."
    return status or "Unknown status."


def first_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:180]
    return ""


def read_run(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def model_label(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    return str(value.get("id") or value.get("model") or "")


def provider_label(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    return str(value.get("provider") or "")


def list_jobs(workspace: Workspace, limit: int = 50) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    runs_root = workspace.rel("runs")
    if not runs_root.exists():
        return jobs
    for path in sorted(runs_root.glob("*.json"), key=lambda item: item.name, reverse=True):
        payload = read_run(path)
        if not payload:
            continue
        packet = payload.get("packet") if isinstance(payload.get("packet"), dict) else {}
        result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        status = str(payload.get("status") or "unknown")
        jobs.append(
            {
                "id": path.stem,
                "agent": str(payload.get("agent") or packet.get("agent", {}).get("id") or ""),
                "runner": str(payload.get("runner") or packet.get("agent", {}).get("runner") or ""),
                "model": model_label(payload.get("model") or packet.get("model") or {}),
                "provider": provider_label(payload.get("model") or packet.get("model") or {}),
                "task": str(payload.get("task") or packet.get("task") or ""),
                "status": status,
                "timestamp": str(payload.get("timestamp") or ""),
                "record": str(path.relative_to(workspace.root)),
                "summary": str(payload.get("summary") or result_summary(status, packet, result)),
                "usage": payload.get("usage") or packet_usage(packet, result),
            }
        )
        if len(jobs) >= limit:
            break
    return jobs


def dashboard_data(workspace: Workspace) -> dict[str, Any]:
    doctor_errors, doctor_warnings = workspace.doctor()
    model_errors, model_warnings = validate_models(workspace)
    skill_errors, skill_warnings = validate_skills(workspace)
    agent_errors, agent_warnings = validate_agents(workspace)
    auth_errors, auth_warnings = validate_auth(workspace)
    api_errors, api_warnings = validate_api(workspace)
    gateway_errors, gateway_warnings = validate_gateway(workspace)
    warnings = warning_rows(
        doctor_errors,
        doctor_warnings,
        model_errors,
        model_warnings,
        skill_errors,
        skill_warnings,
        agent_errors,
        agent_warnings,
    )
    for source, severity, values in [
        ("auth", "critical", auth_errors),
        ("auth", "warning", auth_warnings),
        ("api", "critical", api_errors),
        ("api", "warning", api_warnings),
        ("gateway", "critical", gateway_errors),
        ("gateway", "warning", gateway_warnings),
    ]:
        for value in values:
            warnings.append({"severity": severity, "source": source, "message": value})
    for skill in discover_skills(workspace):
        if not skill.eligible and skill.reason:
            warnings.append(
                {
                    "severity": "warning",
                    "source": f"skill:{skill.name}",
                    "message": skill.reason,
                }
            )

    jobs = list_jobs(workspace)
    usage = aggregate_usage(jobs)
    skills = skill_rows(workspace)
    skill_config = skill_config_rows(workspace)
    agents = agent_rows(workspace)
    models = model_rows(workspace)
    auth = auth_rows(workspace)
    api = api_rows(workspace)
    signals = collect_signals(workspace)
    setup = setup_dashboard_report(
        workspace,
        doctor_errors,
        doctor_warnings,
        model_errors,
        model_warnings,
        auth_errors,
        auth_warnings,
        api_errors,
        api_warnings,
        gateway_errors,
        gateway_warnings,
        skill_errors,
        skill_warnings,
        agent_errors,
        agent_warnings,
        models,
        auth,
        skills,
        skill_config,
    )
    return {
        "root": str(workspace.root),
        "metrics": {
            "runningJobs": sum(1 for job in jobs if job["status"] == "running"),
            "completedJobs": sum(1 for job in jobs if job["status"] in {"ok", "packet-only"}),
            "failedJobs": sum(1 for job in jobs if job["status"] == "failed"),
            "skillsEnabled": sum(1 for row in skills if row["enabled"] == "yes"),
            "skillsTotal": len(skills),
            "agentsTotal": len(agents),
            "modelsTotal": len(models),
            "authProfiles": len(auth),
            "apiProfiles": len(api),
            "warningCount": len(warnings),
            "signals": len(signals),
        },
        "usage": usage,
        "jobs": jobs,
        "warnings": warnings,
        "skills": skills,
        "skillConfig": skill_config,
        "agents": agents,
        "models": models,
        "auth": auth,
        "api": api,
        "gateway": gateway_info(workspace),
        "setup": setup,
        "signals": signals,
        "summary": workspace_summary(jobs, warnings, usage),
    }


def warning_rows(
    doctor_errors: list[str],
    doctor_warnings: list[str],
    model_errors: list[str],
    model_warnings: list[str],
    skill_errors: list[str],
    skill_warnings: list[str],
    agent_errors: list[str],
    agent_warnings: list[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source, severity, values in [
        ("workspace", "critical", doctor_errors),
        ("workspace", "warning", doctor_warnings),
        ("models", "critical", model_errors),
        ("models", "warning", model_warnings),
        ("skills", "critical", skill_errors),
        ("skills", "warning", skill_warnings),
        ("agents", "critical", agent_errors),
        ("agents", "warning", agent_warnings),
    ]:
        for value in values:
            rows.append({"severity": severity, "source": source, "message": value})
    return rows


def setup_dashboard_report(
    workspace: Workspace,
    doctor_errors: list[str],
    doctor_warnings: list[str],
    model_errors: list[str],
    model_warnings: list[str],
    auth_errors: list[str],
    auth_warnings: list[str],
    api_errors: list[str],
    api_warnings: list[str],
    gateway_errors: list[str],
    gateway_warnings: list[str],
    skill_errors: list[str],
    skill_warnings: list[str],
    agent_errors: list[str],
    agent_warnings: list[str],
    models: list[dict[str, str]],
    auth: list[dict[str, str]],
    skills: list[dict[str, str]],
    skill_config: list[dict[str, str]],
) -> dict[str, Any]:
    agent_ids = {str(raw.get("id") or "") for raw in workspace.config.get("agents", {}).get("list", [])}
    rows = [
        setup_row("workspace", doctor_errors, doctor_warnings, "Workspace files, prompt files, and configured roots are present.", "birkin-codex doctor"),
        setup_row("models", model_errors, model_warnings, f"{len(models)} model profiles configured.", "birkin-codex model list"),
        setup_row("auth", auth_errors, auth_warnings, f"{len(auth)} auth profiles configured.", "birkin-codex auth list"),
        setup_row("api", api_errors, api_warnings, "OpenAI-compatible API profiles are configured.", "birkin-codex api list"),
        setup_row("gateway", gateway_errors, gateway_warnings, "Gateway config is available.", "birkin-codex gateway status"),
        setup_row("skills", skill_errors, skill_warnings, f"{sum(1 for row in skills if row['enabled'] == 'yes')}/{len(skills)} skills are enabled and eligible.", "birkin-codex skills validate"),
        setup_row("agents", agent_errors, agent_warnings, "Agent roles and skill allowlists are configured.", "birkin-codex agents list"),
        setup_row("chat", [] if "chat" in agent_ids else ["chat agent is not configured"], [], "Chat agent and dashboard chat API are available.", "birkin-codex web --port 8765"),
    ]
    status = "error" if any(row["status"] == "error" for row in rows) else "warning" if any(
        row["status"] == "warning" for row in rows
    ) else "ok"
    return {"status": status, "checks": rows, "skillConfig": skill_config}


def setup_row(
    step: str,
    errors: list[str],
    warnings: list[str],
    detail: str,
    command: str,
) -> dict[str, str]:
    status = "error" if errors else "warning" if warnings else "ok"
    if errors:
        detail = "; ".join(errors[:2])
    elif warnings:
        detail = detail + " Warning: " + "; ".join(warnings[:2])
    return {"step": step, "status": status, "detail": detail, "command": command}


def aggregate_usage(jobs: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "runs": len(jobs),
        "estimatedTokens": 0,
        "promptChars": 0,
        "promptWords": 0,
        "stdoutChars": 0,
        "stderrChars": 0,
    }
    for job in jobs:
        usage = job.get("usage") or {}
        for key in totals:
            if key == "runs":
                continue
            totals[key] += int(usage.get(key) or 0)
    return totals


def workspace_summary(
    jobs: list[dict[str, Any]],
    warnings: list[dict[str, str]],
    usage: dict[str, int],
) -> str:
    if not jobs:
        return "No job records yet. The workspace is ready for a first dry-run packet."
    latest = jobs[0]
    critical = sum(1 for warning in warnings if warning["severity"] == "critical")
    return (
        f"Latest job {latest['id']} is {latest['status']} for {latest['agent']}. "
        f"{usage['runs']} job records are tracked with about {usage['estimatedTokens']} prompt tokens. "
        f"{critical} critical warnings need attention."
    )
