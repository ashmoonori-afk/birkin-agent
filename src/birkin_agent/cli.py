from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .agents import add_agent, agent_rows, build_packet, run_agent, validate_agents
from .api import add_api_profile, api_rows, validate_api
from .auth import add_auth_profile, auth_rows, run_auth_command, validate_auth
from .chat import run_chat
from .gateway import ROUTES, gateway_info, serve_gateway, validate_gateway
from .improve import append_lesson, apply_improvement, propose_improvement
from .models import add_model_profile, model_rows, use_model_profile, validate_models
from .setup import setup_report, setup_rows
from .skills import create_skill, discover_skills, skill_config_rows, skill_rows, validate_skills
from .util import print_table
from .web import serve
from .workspace import Workspace


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        return cmd_chat_interactive(
            argparse.Namespace(agent=None, model=None, provider=None, execute=False)
        )
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="birkin-codex", description="Birkin Codex agent workspace CLI")
    sub = parser.add_subparsers(required=True)

    init = sub.add_parser("init", help="Initialize a Birkin workspace")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    doctor = sub.add_parser("doctor", help="Check workspace health")
    doctor.set_defaults(func=cmd_doctor)

    add_setup_parser(sub.add_parser("setup", help="Check Hermes-style setup readiness"))
    add_model_parser(sub.add_parser("model", help="Select and configure model profiles"))
    add_model_parser(sub.add_parser("models", help="Select and configure model profiles"))
    add_auth_parser(sub.add_parser("auth", help="Manage local CLI auth profiles"))
    add_api_parser(sub.add_parser("api", help="Manage OpenAI-compatible API profiles"))
    add_gateway_parser(sub.add_parser("gateway", help="Run the Birkin local gateway"))

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
    skills_config = skills_sub.add_parser("config")
    skills_config.add_argument("--json", action="store_true")
    skills_config.set_defaults(func=cmd_skills_config)
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

    chat = sub.add_parser("chat", help="Send a message or open the interactive chat agent")
    chat.add_argument("--message")
    chat.add_argument("--agent")
    chat.add_argument("--model")
    chat.add_argument("--provider")
    chat.add_argument("--execute", action="store_true")
    chat.add_argument("--interactive", "-i", action="store_true")
    chat.add_argument("--json", action="store_true")
    chat.set_defaults(func=cmd_chat)
    return parser


def add_setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true")
    setup_sub = parser.add_subparsers(dest="setup_command")
    setup_check = setup_sub.add_parser("check")
    setup_check.add_argument("--json", action="store_true")
    setup_check.set_defaults(func=cmd_setup_check)
    setup_status = setup_sub.add_parser("status")
    setup_status.add_argument("--json", action="store_true")
    setup_status.set_defaults(func=cmd_setup_check)
    parser.set_defaults(func=cmd_setup_check)


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
    model_add.add_argument("--api-profile", default="")
    model_add.add_argument("--timeout", type=int, default=1800)
    model_add.add_argument("--description", default="")
    model_add.set_defaults(func=cmd_models_add)


def add_auth_parser(parser: argparse.ArgumentParser) -> None:
    auth_sub = parser.add_subparsers(required=True)
    auth_list = auth_sub.add_parser("list")
    auth_list.add_argument("--json", action="store_true")
    auth_list.set_defaults(func=cmd_auth_list)
    auth_status = auth_sub.add_parser("status")
    auth_status.add_argument("id", nargs="?")
    auth_status.add_argument("--json", action="store_true")
    auth_status.set_defaults(func=cmd_auth_status)
    auth_login = auth_sub.add_parser("login")
    auth_login.add_argument("id")
    auth_login.set_defaults(func=cmd_auth_login)
    auth_logout = auth_sub.add_parser("logout")
    auth_logout.add_argument("id")
    auth_logout.add_argument("--json", action="store_true")
    auth_logout.set_defaults(func=cmd_auth_logout)
    auth_add = auth_sub.add_parser("add")
    auth_add.add_argument("id")
    auth_add.add_argument("--type", default="local-cli-oauth")
    auth_add.add_argument("--provider", required=True)
    auth_add.add_argument("--binary", default="")
    auth_add.add_argument("--login-json", default="[]")
    auth_add.add_argument("--logout-json", default="[]")
    auth_add.add_argument("--status-json", default="[]")
    auth_add.add_argument("--description", default="")
    auth_add.add_argument("--required", action="store_true")
    auth_add.set_defaults(func=cmd_auth_add)


def add_api_parser(parser: argparse.ArgumentParser) -> None:
    api_sub = parser.add_subparsers(required=True)
    api_list = api_sub.add_parser("list")
    api_list.add_argument("--json", action="store_true")
    api_list.set_defaults(func=cmd_api_list)
    api_add = api_sub.add_parser("add")
    api_add.add_argument("id")
    api_add.add_argument("--type", default="openai-compatible")
    api_add.add_argument("--base-url", required=True)
    api_add.add_argument("--api-key-env", default="")
    api_add.add_argument("--chat-path", default="/chat/completions")
    api_add.add_argument("--timeout", type=int, default=1800)
    api_add.add_argument("--description", default="")
    api_add.set_defaults(func=cmd_api_add)


def add_gateway_parser(parser: argparse.ArgumentParser) -> None:
    gateway_sub = parser.add_subparsers(required=True)
    gateway_routes = gateway_sub.add_parser("routes")
    gateway_routes.set_defaults(func=cmd_gateway_routes)
    gateway_status = gateway_sub.add_parser("status")
    gateway_status.add_argument("--json", action="store_true")
    gateway_status.set_defaults(func=cmd_gateway_status)
    gateway_run = gateway_sub.add_parser("run")
    gateway_run.add_argument("--host")
    gateway_run.add_argument("--port", type=int)
    gateway_run.set_defaults(func=cmd_gateway_run)


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
    auth_errors, auth_warnings = validate_auth(workspace)
    api_errors, api_warnings = validate_api(workspace)
    gateway_errors, gateway_warnings = validate_gateway(workspace)
    errors.extend(model_errors)
    errors.extend(skill_errors)
    errors.extend(agent_errors)
    errors.extend(auth_errors)
    errors.extend(api_errors)
    errors.extend(gateway_errors)
    warnings.extend(model_warnings)
    warnings.extend(skill_warnings)
    warnings.extend(agent_warnings)
    warnings.extend(auth_warnings)
    warnings.extend(api_warnings)
    warnings.extend(gateway_warnings)
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    if errors:
        return 1
    print("ok")
    return 0


def cmd_setup_check(args: argparse.Namespace) -> int:
    workspace = ws()
    report = setup_report(workspace)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_table(setup_rows(workspace), ["step", "status", "detail", "command"])
        print()
        print_table(skill_config_rows(workspace), ["check", "status", "detail"])
    return 1 if report["status"] == "error" else 0


def cmd_models_list(args: argparse.Namespace) -> int:
    workspace = ws()
    rows = model_rows(workspace)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(
            rows,
            ["id", "default", "provider", "model", "runner", "apiProfile", "command", "description"],
        )
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
        args.api_profile,
    )
    print(f"created model {args.id}")
    return 0


def cmd_auth_list(args: argparse.Namespace) -> int:
    rows = auth_rows(ws())
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["id", "type", "provider", "binary", "available", "required", "description"])
    return 0


def cmd_auth_status(args: argparse.Namespace) -> int:
    workspace = ws()
    if not args.id:
        rows = auth_rows(workspace)
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            print_table(rows, ["id", "type", "provider", "binary", "available", "required", "description"])
        return 0
    result = run_auth_command(workspace, args.id, "status")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["stdout"]:
            print(result["stdout"], end="")
        if result["stderr"]:
            print(result["stderr"], end="", file=sys.stderr)
    return int(result.get("returncode") or 0)


def cmd_auth_login(args: argparse.Namespace) -> int:
    result = run_auth_command(ws(), args.id, "login", interactive=True)
    return int(result.get("returncode") or 0)


def cmd_auth_logout(args: argparse.Namespace) -> int:
    result = run_auth_command(ws(), args.id, "logout")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["stdout"]:
            print(result["stdout"], end="")
        if result["stderr"]:
            print(result["stderr"], end="", file=sys.stderr)
    return int(result.get("returncode") or 0)


def cmd_auth_add(args: argparse.Namespace) -> int:
    add_auth_profile(
        ws(),
        args.id,
        args.type,
        args.provider,
        args.binary,
        args.login_json,
        args.logout_json,
        args.status_json,
        args.description,
        args.required,
    )
    print(f"created auth profile {args.id}")
    return 0


def cmd_api_list(args: argparse.Namespace) -> int:
    rows = api_rows(ws())
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["id", "type", "baseUrl", "apiKeyEnv", "keyPresent", "chatPath", "description"])
    return 0


def cmd_api_add(args: argparse.Namespace) -> int:
    add_api_profile(
        ws(),
        args.id,
        args.type,
        args.base_url,
        args.api_key_env,
        args.chat_path,
        args.timeout,
        args.description,
    )
    print(f"created api profile {args.id}")
    return 0


def cmd_gateway_routes(args: argparse.Namespace) -> int:
    for route in ROUTES:
        print(route)
    return 0


def cmd_gateway_status(args: argparse.Namespace) -> int:
    info = gateway_info(ws())
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print_table(
            [
                {
                    "host": info["host"],
                    "port": str(info["port"]),
                    "authRequired": "yes" if info["authRequired"] else "no",
                    "tokenEnv": info["tokenEnv"],
                    "routes": str(len(info["routes"])),
                }
            ],
            ["host", "port", "authRequired", "tokenEnv", "routes"],
        )
    return 0


def cmd_gateway_run(args: argparse.Namespace) -> int:
    serve_gateway(ws(), args.host, args.port)
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


def cmd_skills_config(args: argparse.Namespace) -> int:
    rows = skill_config_rows(ws())
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["check", "status", "detail"])
    return 1 if any(row["status"] == "error" for row in rows) else 0


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


def cmd_chat(args: argparse.Namespace) -> int:
    if args.interactive or not args.message:
        if args.json and not args.message:
            print("error: --json chat requires --message", file=sys.stderr)
            return 1
        return cmd_chat_interactive(args)
    payload = run_chat(
        ws(),
        args.message,
        agent_id=args.agent,
        model_name=args.model,
        provider_name=args.provider,
        execute=args.execute,
    )
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload["reply"])
        print(f"record {payload['record']}")
    return 0 if payload["status"] in {"ok", "packet-only"} else 1


def cmd_chat_interactive(args: argparse.Namespace) -> int:
    workspace = ws()
    agent_id = args.agent
    model_name = args.model
    provider_name = args.provider
    execute = bool(args.execute)
    history: list[dict[str, str]] = []

    print("Birkin Codex")
    print("Type a message to chat. Commands: /help, /setup, /skills, /model ID, /execute on|off, /exit")
    print(f"agent={agent_id or 'chat'} model={model_name or 'default'} execute={'on' if execute else 'off'}")

    while True:
        try:
            message = input("you> ").strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\nbye")
            return 0

        if not message:
            continue
        lowered = message.lower()
        if lowered in {"/exit", "/quit", "exit", "quit"}:
            print("bye")
            return 0
        if lowered == "/help":
            print("Commands:")
            print("  /setup          show setup readiness")
            print("  /skills         show skill configuration checks")
            print("  /model ID       switch model profile for this chat")
            print("  /execute on     allow the selected runner to execute")
            print("  /execute off    packet-only safe mode")
            print("  /exit           leave chat")
            continue
        if lowered == "/setup":
            print_table(setup_rows(workspace), ["step", "status", "detail", "command"])
            continue
        if lowered == "/skills":
            print_table(skill_config_rows(workspace), ["check", "status", "detail"])
            continue
        if lowered.startswith("/model "):
            model_name = message.split(maxsplit=1)[1].strip()
            print(f"model={model_name}")
            continue
        if lowered.startswith("/execute "):
            value = message.split(maxsplit=1)[1].strip().lower()
            if value not in {"on", "off"}:
                print("usage: /execute on|off")
                continue
            execute = value == "on"
            print(f"execute={'on' if execute else 'off'}")
            continue

        try:
            payload = run_chat(
                workspace,
                message,
                agent_id=agent_id,
                model_name=model_name,
                provider_name=provider_name,
                execute=execute,
                history=history,
            )
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            continue

        reply = payload["reply"]
        print(f"birkin> {reply}")
        print(f"record {payload['record']}")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
