from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any

from .api import call_openai_compatible
from .models import render_model_command, resolve_model_profile
from .skills import SkillRecord, discover_skills, parse_frontmatter
from .util import slugify, utc_stamp, write_json
from .workspace import Workspace


@dataclass
class AgentRecord:
    id: str
    role: str
    runner: str
    model: str | None
    skills: list[str] | None
    workspace: str


def list_agents(workspace: Workspace) -> list[AgentRecord]:
    defaults = workspace.config.get("agents", {}).get("defaults", {})
    agents = []
    for raw in workspace.config.get("agents", {}).get("list", []):
        agents.append(
            AgentRecord(
                id=str(raw.get("id")),
                role=str(raw.get("role", "")),
                runner=str(raw.get("runner") or defaults.get("runner") or "dry-run"),
                model=raw.get("model") or defaults.get("model"),
                skills=raw.get("skills", defaults.get("skills")),
                workspace=str(raw.get("workspace") or defaults.get("workspace") or "."),
            )
        )
    return agents


def get_agent(workspace: Workspace, agent_id: str) -> AgentRecord:
    for agent in list_agents(workspace):
        if agent.id == agent_id:
            return agent
    raise KeyError(f"agent not found: {agent_id}")


def add_agent(
    workspace: Workspace,
    agent_id: str,
    role: str,
    skills: list[str] | None,
    runner: str = "dry-run",
    model: str | None = None,
) -> None:
    agents = workspace.config.setdefault("agents", {}).setdefault("list", [])
    if any(raw.get("id") == agent_id for raw in agents):
        raise FileExistsError(f"agent already exists: {agent_id}")
    agents.append({"id": agent_id, "role": role, "skills": skills, "runner": runner, "model": model})
    workspace.save_config()


def eligible_skill_map(workspace: Workspace) -> dict[str, SkillRecord]:
    return {
        skill.name: skill
        for skill in discover_skills(workspace)
        if skill.enabled and skill.eligible
    }


def select_skills(workspace: Workspace, agent: AgentRecord) -> list[SkillRecord]:
    available = eligible_skill_map(workspace)
    if agent.skills is None:
        return sorted(available.values(), key=lambda item: item.name)
    return [available[name] for name in agent.skills if name in available]


def compact_skill_catalog(skills: list[SkillRecord]) -> str:
    if not skills:
        return "<available_skills />"
    lines = ["<available_skills>"]
    for skill in skills:
        location = skill.path.parent.as_posix()
        description = skill.description.replace('"', "'")
        lines.append(
            f'  <skill name="{skill.name}" description="{description}" location="{location}" />'
        )
    lines.append("</available_skills>")
    return "\n".join(lines)


def load_prompt_files(workspace: Workspace) -> str:
    parts: list[str] = []
    for rel_path in workspace.config.get("workspace", {}).get("promptFiles", []):
        path = workspace.rel(rel_path)
        if path.exists():
            parts.append(f"## {rel_path}\n\n{path.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(parts)


def skill_bodies(skills: list[SkillRecord]) -> str:
    bodies: list[str] = []
    for skill in skills:
        _frontmatter, body, _issues = parse_frontmatter(skill.path)
        bodies.append(f"## Skill: {skill.name}\n\n{body.strip()}")
    return "\n\n".join(bodies)


def build_packet(
    workspace: Workspace,
    agent_id: str,
    task: str,
    include_skill_bodies: bool = False,
    model_name: str | None = None,
    provider_name: str | None = None,
    runner_name: str | None = None,
) -> dict[str, Any]:
    agent = get_agent(workspace, agent_id)
    profile = resolve_model_profile(workspace, model_name or agent.model, provider_name)
    runner_key = runner_name or profile.runner or agent.runner
    skills = select_skills(workspace, agent)
    packet = {
        "workspace": str(workspace.root),
        "agent": {
            "id": agent.id,
            "role": agent.role,
            "runner": runner_key,
            "model": profile.id,
            "skillAllowlist": agent.skills,
        },
        "model": {
            "id": profile.id,
            "provider": profile.provider,
            "model": profile.model,
            "runner": runner_key,
            "apiProfile": profile.api_profile,
            "description": profile.description,
        },
        "task": task,
        "prompt": "\n\n".join(
            part
            for part in [
                load_prompt_files(workspace),
                compact_skill_catalog(skills),
                "## Task\n\n" + task,
                skill_bodies(skills) if include_skill_bodies else "",
            ]
            if part
        ),
        "skills": [
            {
                "name": skill.name,
                "description": skill.description,
                "location": str(skill.path.parent),
                "source": skill.source,
            }
            for skill in skills
        ],
    }
    return packet


def save_run_record(
    workspace: Workspace,
    agent_id: str,
    task: str,
    runner: str,
    status: str,
    packet: dict[str, Any],
    result: dict[str, Any] | None = None,
) -> Path:
    path = workspace.rel("runs", f"{utc_stamp()}_{slugify(agent_id)}.json")
    usage = packet_usage(packet, result)
    summary = summarize_result(status, packet, result or {})
    write_json(
        path,
        {
            "timestamp": utc_stamp(),
            "agent": agent_id,
            "runner": runner,
            "model": packet.get("model") or {},
            "task": task,
            "status": status,
            "summary": summary,
            "usage": usage,
            "packet": packet,
            "result": result or {},
        },
    )
    return path


def packet_usage(packet: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, int]:
    result = result or {}
    prompt = str(packet.get("prompt") or "")
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    return {
        "promptChars": len(prompt),
        "promptWords": len(prompt.split()),
        "estimatedTokens": max(1, (len(prompt) + 3) // 4) if prompt else 0,
        "skills": len(packet.get("skills") or []),
        "stdoutChars": len(stdout),
        "stderrChars": len(stderr),
    }


def summarize_result(status: str, packet: dict[str, Any], result: dict[str, Any]) -> str:
    if status == "packet-only":
        return f"Prompt packet built with {len(packet.get('skills') or [])} skills; no model runner executed."
    if status == "ok":
        return first_nonempty_line(str(result.get("stdout") or "")) or "Runner finished successfully."
    if status == "failed":
        return (
            first_nonempty_line(str(result.get("stderr") or ""))
            or first_nonempty_line(str(result.get("stdout") or ""))
            or "Runner failed without output."
        )
    return status


def first_nonempty_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:180]
    return ""


def run_agent(
    workspace: Workspace,
    agent_id: str,
    task: str,
    runner_name: str | None = None,
    model_name: str | None = None,
    provider_name: str | None = None,
    include_skill_bodies: bool = False,
    execute: bool = False,
) -> tuple[Path, dict[str, Any]]:
    packet = build_packet(
        workspace,
        agent_id,
        task,
        include_skill_bodies,
        model_name=model_name,
        provider_name=provider_name,
        runner_name=runner_name,
    )
    runner_key = str(packet.get("agent", {}).get("runner") or runner_name or "dry-run")
    runner = workspace.config.get("runners", {}).get(runner_key)
    if not runner:
        raise KeyError(f"runner not found: {runner_key}")

    runner_type = str(runner.get("type") or "")
    if runner_type == "packet" or not execute:
        record = save_run_record(workspace, agent_id, task, runner_key, "packet-only", packet)
        return record, {"packet": packet, "executed": False}

    profile = resolve_model_profile(
        workspace,
        str(packet.get("model", {}).get("id") or model_name or ""),
        str(packet.get("model", {}).get("provider") or provider_name or ""),
    )
    if runner_type == "api":
        api_profile = profile.api_profile or str(runner.get("profile") or "")
        timeout = int(profile.timeout_seconds or runner.get("timeoutSeconds") or 1800)
        result = call_openai_compatible(
            workspace,
            api_profile,
            packet["prompt"],
            profile.model,
            timeout_seconds=timeout,
        )
        status = "ok" if result.get("returncode") == 0 else "failed"
        record = save_run_record(workspace, agent_id, task, runner_key, status, packet, result)
        return record, result

    command = profile.command or runner.get("command")
    if not isinstance(command, list) or not command:
        raise ValueError(
            f"model {profile.id} or runner {runner_key} requires a non-empty argv list"
        )
    timeout = int(profile.timeout_seconds or runner.get("timeoutSeconds") or 1800)
    completed = subprocess.run(
        render_model_command([str(part) for part in command], profile),
        input=packet["prompt"],
        text=True,
        capture_output=True,
        cwd=workspace.root,
        timeout=timeout,
        check=False,
    )
    result = {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    status = "ok" if completed.returncode == 0 else "failed"
    record = save_run_record(workspace, agent_id, task, runner_key, status, packet, result)
    return record, result


def agent_rows(workspace: Workspace) -> list[dict[str, str]]:
    return [
        {
            "id": agent.id,
            "runner": agent.runner,
            "model": agent.model or "",
            "skills": "*" if agent.skills is None else ",".join(agent.skills),
            "role": agent.role,
        }
        for agent in list_agents(workspace)
    ]


def validate_agents(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    discovered = {skill.name: skill for skill in discover_skills(workspace)}
    eligible = eligible_skill_map(workspace)
    for agent in list_agents(workspace):
        if not agent.id:
            errors.append("agent missing id")
        if agent.runner not in workspace.config.get("runners", {}):
            errors.append(f"{agent.id}: runner not found: {agent.runner}")
        if agent.model:
            try:
                resolve_model_profile(workspace, agent.model)
            except KeyError:
                errors.append(f"{agent.id}: model profile not found: {agent.model}")
        if agent.skills is None:
            continue
        for skill_name in agent.skills:
            if skill_name not in discovered:
                errors.append(f"{agent.id}: configured skill not found: {skill_name}")
            elif skill_name not in eligible:
                warnings.append(f"{agent.id}: configured skill is disabled or gated: {skill_name}")
    return errors, warnings
