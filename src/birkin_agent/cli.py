from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .agents import add_agent, agent_rows, build_packet, run_agent, validate_agents
from .improve import append_lesson, apply_improvement, propose_improvement
from .models import add_model_profile, model_rows, use_model_profile, validate_models
from .skills import create_skill, discover_skills, skill_rows, validate_skills
from .util import print_table
from .web import serve
from .workspace import Workspace


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="birkin", description="Birkin agent workspace CLI")
    sub = parser.add_subparsers(required=True)

    init = sub.add_parser("init", help="Initialize a Birkin workspace")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    doctor = sub.add_parser("doctor", help="Check workspace health")
    doctor.set_defaults(func=cmd_doctor)

    add_model_parser(sub.add_parser("model", help="Select and configure model profiles"))
    add_model_parser(sub.add_parser("models", help="Select and configure model profiles"))

    skills = sub.add_parser("skills", help="Manage skills")
    skills_sub = skills.add_subparsers(required=True)
    skills_list = skills_sub.add_parser("list")
    skills_list.add_argument("--json", action="store_true")
    skills_list.set_defaults(func=cmd_skills_list)
    skills_show = skills_sub.add_parser("show")
    skills_show.add_argument("name")
    skills_show.set_defaults(func=cmd_skills_show)
    skills_validate = skills_sub.add_parser("validate")
    skills_validate.set_defaults(func=cmd_skills_validate)
    skills_create = skills_sub.add_parser("create")
    skills_create.add_argument("name")
    skills_create.add_argument("--description", required=True)
    skills_create.add_argument("--group", default="custom")
    skills_create.set_defaults(func=cmd_skills_create)
    skills_enable = skills_sub.add_parser("enable")
    skills_enable.add_argument("name")
    skills_enable.set_defaults(func=cmd_skills_enable)
    skills_disable = skills_sub.add_parser("disable")
    skills_disable.add_argument("name")
    skills_disable.set_defaults(func=cmd_skills_disable)

    agents = sub.add_parser("agents", help="Manage subagents")
    agents_sub = agents.add_subparsers(required=True)
    agents_list = agents_sub.add_parser("list")
    agents_list.set_defaults(func=cmd_agents_list)
    agents_create = agents_sub.add_parser("create")
    agents_create.add_argument("id")
    agents_create.add_argument("--role", required=True)
    agents_create.add_argument("--skills", default=None, help="Comma-separated final allowlist. Omit for all.")
    agents_create.add_argument("--runner", default="dry-run")
    agents_create.add_argument("--model")
    agents_create.set_defaults(func=cmd_agents_create)
    packet = agents_sub.add_parser("packet")
    packet.add_argument("id")
    packet.add_argument("--task", required=True)
    packet.add_argument("--model")
    packet.add_argument("--provider")
    packet.add_argument("--runner")
    packet.add_argument("--include-skill-bodies", action="store_true")
    packet.set_defaults(func=cmd_agents_packet)
    run = agents_sub.add_parser("run")
    run.add_argument("id")
    run.add_argument("--task", required=True)
    run.add_argument("--runner")
    run.add_argument("--model")
    run.add_argument("--provider")
    run.add_argument("--execute", action="store_true")
    run.add_argument("--include-skill-bodies", action="store_true")
    run.set_defaults(func=cmd_agents_run)

    improve = sub.add_parser("improve", help="Record and apply self-improvement proposals")
    improve_sub = improve.add_subparsers(required=True)
    record = improve_sub.add_parser("record")
    record.add_argument("--lesson", required=True)
    record.add_argument("--skill")
    record.set_defaults(func=cmd_improve_record)
    propose = improve_sub.add_parser("propose")
    propose.add_argument("--lesson")
    propose.add_argument("--skill")
    propose.set_defaults(func=cmd_improve_propose)
    apply_cmd = improve_sub.add_parser("apply")
    apply_cmd.add_argument("proposal")
    apply_cmd.add_argument("--skill", required=True)
    apply_cmd.add_argument("--yes", action="store_true")
    apply_cmd.set_defaults(func=cmd_improve_apply)

    web = sub.add_parser("web", help="Open the lightweight Web UI server")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8765)
    web.set_defaults(func=cmd_web)
    return parser


def add_model_parser(parser: argparse.ArgumentParser) -> None:
    model_sub = parser.add_subparsers(required=True)
    model_list = model_sub.add_parser("list")
    model_list.add_argument("--json", action="store_true")
    model_list.set_defaults(func=cmd_models_list)
    model_use = model_sub.add_parser("use")
    model_use.add_argument("id")
    model_use.set_defaults(func=cmd_models_use)
    model_add = model_sub.add_parser("add")
    model_add.add_argument("id")
    model_add.add_argument("--provider", required=True)
    model_add.add_argument("--model", required=True)
    model_add.add_argument("--runner", default="local-cli")
    model_add.add_argument("--command-json", default="[]")
    model_add.add_argument("--timeout", type=int, default=1800)
    model_add.add_argument("--description", default="")
    model_add.set_defaults(func=cmd_models_add)


def ws() -> Workspace:
    return Workspace.discover(Path.cwd())


def cmd_init(args: argparse.Namespace) -> int:
    workspace = Workspace(Path(args.path))
    created = workspace.init(force=args.force)
    print(f"Workspace: {workspace.root}")
    for path in created:
        print(f"created {path.relative_to(workspace.root)}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    workspace = ws()
    errors, warnings = workspace.doctor()
    model_errors, model_warnings = validate_models(workspace)
    skill_errors, skill_warnings = validate_skills(workspace)
    agent_errors, agent_warnings = validate_agents(workspace)
    errors.extend(model_errors)
    errors.extend(skill_errors)
    errors.extend(agent_errors)
    warnings.extend(model_warnings)
    warnings.extend(skill_warnings)
    warnings.extend(agent_warnings)
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    if errors:
        return 1
    print("ok")
    return 0


def cmd_models_list(args: argparse.Namespace) -> int:
    workspace = ws()
    rows = model_rows(workspace)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["id", "default", "provider", "model", "runner", "command", "description"])
    return 0


def cmd_models_use(args: argparse.Namespace) -> int:
    use_model_profile(ws(), args.id)
    print(f"model default {args.id}")
    return 0


def cmd_models_add(args: argparse.Namespace) -> int:
    add_model_profile(
        ws(),
        args.id,
        args.provider,
        args.model,
        args.runner,
        args.command_json,
        args.timeout,
        args.description,
    )
    print(f"created model {args.id}")
    return 0


def cmd_skills_list(args: argparse.Namespace) -> int:
    workspace = ws()
    rows = skill_rows(workspace)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["name", "enabled", "source", "description", "reason"])
    return 0


def cmd_skills_show(args: argparse.Namespace) -> int:
    workspace = ws()
    for skill in discover_skills(workspace):
        if skill.name == args.name:
            print(skill.path.read_text(encoding="utf-8"))
            return 0
    print(f"skill not found: {args.name}", file=sys.stderr)
    return 1


def cmd_skills_validate(args: argparse.Namespace) -> int:
    workspace = ws()
    errors, warnings = validate_skills(workspace)
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    if errors:
        return 1
    print("ok")
    return 0


def cmd_skills_create(args: argparse.Namespace) -> int:
    path = create_skill(ws(), args.name, args.description, args.group)
    print(path)
    return 0


def cmd_skills_enable(args: argparse.Namespace) -> int:
    workspace = ws()
    skill_config = workspace.config.setdefault("skills", {})
    disabled = set(skill_config.get("disabled") or [])
    disabled.discard(args.name)
    skill_config["disabled"] = sorted(disabled)
    enabled = skill_config.get("enabled")
    if isinstance(enabled, list) and args.name not in enabled:
        enabled.append(args.name)
        skill_config["enabled"] = sorted(enabled)
    workspace.save_config()
    print(f"enabled {args.name}")
    return 0


def cmd_skills_disable(args: argparse.Namespace) -> int:
    workspace = ws()
    skill_config = workspace.config.setdefault("skills", {})
    disabled = set(skill_config.get("disabled") or [])
    disabled.add(args.name)
    skill_config["disabled"] = sorted(disabled)
    workspace.save_config()
    print(f"disabled {args.name}")
    return 0


def parse_skill_arg(value: str | None) -> list[str] | None:
    if value is None:
        return None
    if value.strip() == "":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def cmd_agents_list(args: argparse.Namespace) -> int:
    print_table(agent_rows(ws()), ["id", "runner", "model", "skills", "role"])
    return 0


def cmd_agents_create(args: argparse.Namespace) -> int:
    add_agent(ws(), args.id, args.role, parse_skill_arg(args.skills), args.runner, args.model)
    print(f"created {args.id}")
    return 0


def cmd_agents_packet(args: argparse.Namespace) -> int:
    packet = build_packet(
        ws(),
        args.id,
        args.task,
        args.include_skill_bodies,
        model_name=args.model,
        provider_name=args.provider,
        runner_name=args.runner,
    )
    print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


def cmd_agents_run(args: argparse.Namespace) -> int:
    record, result = run_agent(
        ws(),
        args.id,
        args.task,
        runner_name=args.runner,
        model_name=args.model,
        provider_name=args.provider,
        include_skill_bodies=args.include_skill_bodies,
        execute=args.execute,
    )
    print(f"record {record}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("returncode", 0) == 0 else 1


def cmd_improve_record(args: argparse.Namespace) -> int:
    path = append_lesson(ws(), args.lesson, args.skill)
    print(path)
    return 0


def cmd_improve_propose(args: argparse.Namespace) -> int:
    path = propose_improvement(ws(), args.lesson, args.skill)
    print(path)
    return 0


def cmd_improve_apply(args: argparse.Namespace) -> int:
    path = apply_improvement(ws(), args.proposal, args.skill, args.yes)
    print(path)
    return 0


def cmd_web(args: argparse.Namespace) -> int:
    serve(ws(), args.host, args.port)
    return 0
