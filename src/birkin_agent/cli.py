from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from .agents import add_agent, agent_rows, build_packet, run_agent, validate_agents
from .api import add_api_profile, api_rows, validate_api
from .auth import add_auth_profile, auth_rows, run_auth_command, validate_auth
from .chat import run_chat
from .experience import current_experience, is_optional_lite_warning, set_experience_mode
from .gateway import ROUTES, gateway_info, serve_gateway, validate_gateway
from .improve import append_lesson, apply_improvement, propose_improvement
from .learning import (
    approve_learning,
    learning_event_rows,
    learning_proposal_rows,
    reject_learning,
    rollback_learning,
    show_learning_proposal,
)
from .ledger import ledger_rows, ledger_summary
from .approvals import approval_rows, approve, reject
from .memory import (
    configure_obsidian_vault,
    memory_get_note,
    memory_link,
    memory_search,
    memory_status,
    memory_write_note,
    recall_memory,
    record_feedback,
    validate_memory,
)
from .models import add_model_profile, default_model_id, model_profile_map, model_rows, use_model_profile, validate_models
from .morpheus import run_morpheus
from .presets import is_lite
from .reliability import budget_status, health_checks, reliability_rows, trace_rows
from .runtime_deps import validate_runtime_dependencies
from .scheduler import daemon_status, run_daemon, schedule_rows
from .setup import setup_report, setup_rows
from .skills import create_skill, discover_skills, ensure_bundled_skills, skill_config_rows, skill_rows, skill_safety_rows, validate_skills
from .telegram import configure_telegram, send_telegram_message, telegram_status, validate_telegram
from .util import print_table
from .web import serve
from .wizard import setup_wizard
from .workspace import Workspace


BIRKIN_STARTUP_ART = r"""██████╗ ██╗██████╗ ██╗  ██╗██╗███╗   ██╗
██╔══██╗██║██╔══██╗██║ ██╔╝██║████╗  ██║
██████╔╝██║██████╔╝█████╔╝ ██║██╔██╗ ██║
██╔══██╗██║██╔══██╗██╔═██╗ ██║██║╚██╗██║
██████╔╝██║██║  ██║██║  ██╗██║██║ ╚████║
╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝"""


SLASH_COMMANDS = [
    {"command": "/", "usage": "/", "description": "Show the command picker."},
    {"command": "/help", "usage": "/help", "description": "Show available commands."},
    {"command": "/live", "usage": "/live", "description": "Select the best available live model and enable execution."},
    {"command": "/setup", "usage": "/setup", "description": "Show setup readiness checks."},
    {"command": "/dashboard", "usage": "/dashboard", "description": "Show the dashboard command and local URL."},
    {"command": "/skills", "usage": "/skills", "description": "Show skill catalog health after auto-repairing bundled skills."},
    {"command": "/mode", "usage": "/mode lite|full", "description": "Switch between the small default surface and full operator mode."},
    {"command": "/model", "usage": "/model PROFILE", "description": "Switch the model profile for this chat."},
    {"command": "/execute", "usage": "/execute on|off", "description": "Allow or block runner execution."},
    {"command": "/status", "usage": "/status", "description": "Show the active chat model, mode, skills, and vault."},
    {"command": "/exit", "usage": "/exit", "description": "Leave chat."},
]


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        return cmd_chat_interactive(
            argparse.Namespace(agent=None, model=None, provider=None, execute=False)
        )
    if argv[0] == "nightly":
        argv = ["morpheus", *argv[1:]]
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
    doctor.add_argument("--advanced", action="store_true", help="Include optional auth, API, gateway, and Telegram checks.")
    doctor.set_defaults(func=cmd_doctor)

    add_setup_parser(sub.add_parser("setup", help="Check Hermes-style setup readiness"))
    add_mode_parser(sub.add_parser("mode", help="Switch between lite and full experience modes"))
    add_model_parser(sub.add_parser("model", help="Select and configure model profiles"))
    add_model_parser(sub.add_parser("models", help="Select and configure model profiles"))
    add_auth_parser(sub.add_parser("auth", help="Manage local CLI auth profiles"))
    add_api_parser(sub.add_parser("api", help="Manage OpenAI-compatible API profiles"))
    add_gateway_parser(sub.add_parser("gateway", help="Run the Birkin local gateway"))
    add_memory_parser(sub.add_parser("memory", help="Manage Obsidian-backed memory"))
    add_ledger_parser(sub.add_parser("ledger", help="Inspect usage ledger"))
    add_telegram_parser(sub.add_parser("telegram", help="Configure Telegram onboarding"))
    add_approvals_parser(sub.add_parser("approvals", help="Review pending consequential actions"))
    add_learning_parser(sub.add_parser("learning", help="Review verified-learning proposals and events"))
    add_reliability_parser(sub.add_parser("reliability", help="Inspect traces, health, and budget"))
    add_morpheus_parser(sub.add_parser("morpheus", help="Run the Morpheus self-improvement pass"))
    add_daemon_parser(sub.add_parser("daemon", help="Run the portable Birkin daemon"))

    wizard = sub.add_parser("wizard", help="Run the first-run setup wizard")
    add_wizard_args(wizard)
    wizard.set_defaults(func=cmd_setup_wizard)

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
    skills_safety = skills_sub.add_parser("safety")
    skills_safety.add_argument("--json", action="store_true")
    skills_safety.set_defaults(func=cmd_skills_safety)
    skills_create = skills_sub.add_parser("create")
    skills_create.add_argument("name")
    skills_create.add_argument("--description", required=True)
    skills_create.add_argument("--group", default="custom")
    skills_create.set_defaults(func=cmd_skills_create)
    skills_sync = skills_sub.add_parser("sync")
    skills_sync.add_argument("--from", dest="source", default="")
    skills_sync.add_argument("--json", action="store_true")
    skills_sync.set_defaults(func=cmd_skills_sync)
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
    packet.add_argument("--format", choices=["json", "prompt", "summary"], default="json")
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
    chat.add_argument("--dry-run", action="store_true", help="Force packet-safe mode and make no model call.")
    chat.add_argument("--interactive", "-i", action="store_true")
    chat.add_argument("--json", action="store_true")
    chat.set_defaults(func=cmd_chat)
    return parser


def add_setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--advanced", action="store_true")
    setup_sub = parser.add_subparsers(dest="setup_command")
    setup_check = setup_sub.add_parser("check")
    setup_check.add_argument("--json", action="store_true")
    setup_check.add_argument("--advanced", action="store_true")
    setup_check.set_defaults(func=cmd_setup_check)
    setup_status = setup_sub.add_parser("status")
    setup_status.add_argument("--json", action="store_true")
    setup_status.add_argument("--advanced", action="store_true")
    setup_status.set_defaults(func=cmd_setup_check)
    setup_wizard_parser = setup_sub.add_parser("wizard")
    add_wizard_args(setup_wizard_parser)
    setup_wizard_parser.set_defaults(func=cmd_setup_wizard)
    parser.set_defaults(func=cmd_setup_check)


def add_mode_parser(parser: argparse.ArgumentParser) -> None:
    mode_sub = parser.add_subparsers(required=True)
    status = mode_sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_mode_status)
    use = mode_sub.add_parser("use")
    use.add_argument("mode", choices=["lite", "full"])
    use.add_argument("--json", action="store_true")
    use.set_defaults(func=cmd_mode_use)


def add_wizard_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model")
    parser.add_argument("--obsidian-vault")
    parser.add_argument("--telegram-chat-id")
    parser.add_argument("--telegram-token-env", default="TELEGRAM_BOT_TOKEN")
    parser.add_argument("--enable-telegram", action="store_true")
    parser.add_argument("--enable-telegram-inbound", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")


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


def add_memory_parser(parser: argparse.ArgumentParser) -> None:
    memory_sub = parser.add_subparsers(required=True)
    status = memory_sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_memory_status)
    set_vault = memory_sub.add_parser("set-vault")
    set_vault.add_argument("path")
    set_vault.add_argument("--allow-external", action="store_true")
    set_vault.set_defaults(func=cmd_memory_set_vault)
    record = memory_sub.add_parser("record")
    record.add_argument(
        "--kind",
        default="feedback",
        choices=["feedback", "errors", "conversations", "runs", "user", "project", "environment", "workflow", "ephemeral", "negative"],
    )
    record.add_argument("--text", required=True)
    record.set_defaults(func=cmd_memory_record)
    recall = memory_sub.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--json", action="store_true")
    recall.set_defaults(func=cmd_memory_recall)
    search = memory_sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--type")
    search.add_argument("--scope")
    search.add_argument("--min-confidence", type=float)
    search.add_argument("--tag")
    search.add_argument("--source")
    search.add_argument("--include-expired", action="store_true")
    search.add_argument("--json", action="store_true")
    search.set_defaults(func=cmd_memory_search)
    write = memory_sub.add_parser("write-note")
    write.add_argument("--title", required=True)
    write.add_argument("--body", required=True)
    write.add_argument(
        "--kind",
        default="feedback",
        choices=["feedback", "errors", "conversations", "runs", "user", "project", "environment", "workflow", "ephemeral", "negative"],
    )
    write.add_argument("--type", default="topic")
    write.add_argument("--confidence", type=float, default=0.7)
    write.add_argument("--ttl-days", type=int)
    write.add_argument("--scope", action="append", default=[], help="Scope key=value, repeatable.")
    write.add_argument("--author", default="user")
    write.add_argument("--agent", default="")
    write.add_argument("--reason", default="manual memory write")
    write.add_argument("--blame", default="")
    write.add_argument("--expected-version", type=int)
    write.add_argument("--tag", action="append", default=[])
    write.add_argument("--source", action="append", default=[])
    write.add_argument("--link", action="append", default=[])
    write.add_argument("--append", action="store_true")
    write.set_defaults(func=cmd_memory_write_note)
    get_note = memory_sub.add_parser("get-note")
    get_note.add_argument("title")
    get_note.add_argument("--json", action="store_true")
    get_note.set_defaults(func=cmd_memory_get_note)
    link = memory_sub.add_parser("link")
    link.add_argument("--from-title", required=True)
    link.add_argument("--to-title", required=True)
    link.set_defaults(func=cmd_memory_link)


def add_ledger_parser(parser: argparse.ArgumentParser) -> None:
    ledger_sub = parser.add_subparsers(required=True)
    summary = ledger_sub.add_parser("summary")
    summary.add_argument("--json", action="store_true")
    summary.set_defaults(func=cmd_ledger_summary)
    list_cmd = ledger_sub.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")
    list_cmd.add_argument("--limit", type=int, default=50)
    list_cmd.set_defaults(func=cmd_ledger_list)


def add_telegram_parser(parser: argparse.ArgumentParser) -> None:
    telegram_sub = parser.add_subparsers(required=True)
    status = telegram_sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_telegram_status)
    setup = telegram_sub.add_parser("setup")
    setup.add_argument("--chat-id", required=True)
    setup.add_argument("--token-env", default="TELEGRAM_BOT_TOKEN")
    setup.add_argument("--enable", action="store_true")
    setup.add_argument("--enable-inbound", action="store_true")
    setup.set_defaults(func=cmd_telegram_setup)
    test = telegram_sub.add_parser("test")
    test.add_argument("--message", default="Birkin Codex Telegram onboarding test.")
    test.add_argument("--json", action="store_true")
    test.set_defaults(func=cmd_telegram_test)
    poll = telegram_sub.add_parser("poll")
    poll.add_argument("--once", action="store_true")
    poll.add_argument("--json", action="store_true")
    poll.set_defaults(func=cmd_telegram_poll)


def add_approvals_parser(parser: argparse.ArgumentParser) -> None:
    approvals_sub = parser.add_subparsers(required=True)
    list_cmd = approvals_sub.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")
    list_cmd.set_defaults(func=cmd_approvals_list)
    approve_cmd = approvals_sub.add_parser("approve")
    approve_cmd.add_argument("id")
    approve_cmd.add_argument("--json", action="store_true")
    approve_cmd.set_defaults(func=cmd_approvals_approve)
    reject_cmd = approvals_sub.add_parser("reject")
    reject_cmd.add_argument("id")
    reject_cmd.add_argument("--json", action="store_true")
    reject_cmd.set_defaults(func=cmd_approvals_reject)


def add_learning_parser(parser: argparse.ArgumentParser) -> None:
    learning_sub = parser.add_subparsers(required=True)
    list_cmd = learning_sub.add_parser("list")
    list_cmd.add_argument("--json", action="store_true")
    list_cmd.set_defaults(func=cmd_learning_list)
    events = learning_sub.add_parser("events")
    events.add_argument("--json", action="store_true")
    events.add_argument("--limit", type=int, default=50)
    events.set_defaults(func=cmd_learning_events)
    show = learning_sub.add_parser("show")
    show.add_argument("id")
    show.set_defaults(func=cmd_learning_show)
    approve_cmd = learning_sub.add_parser("approve")
    approve_cmd.add_argument("id")
    approve_cmd.add_argument("--json", action="store_true")
    approve_cmd.set_defaults(func=cmd_learning_approve)
    reject_cmd = learning_sub.add_parser("reject")
    reject_cmd.add_argument("id")
    reject_cmd.add_argument("--json", action="store_true")
    reject_cmd.set_defaults(func=cmd_learning_reject)
    rollback_cmd = learning_sub.add_parser("rollback")
    rollback_cmd.add_argument("event_id")
    rollback_cmd.add_argument("--json", action="store_true")
    rollback_cmd.set_defaults(func=cmd_learning_rollback)


def add_reliability_parser(parser: argparse.ArgumentParser) -> None:
    reliability_sub = parser.add_subparsers(required=True)
    health = reliability_sub.add_parser("health")
    health.add_argument("--json", action="store_true")
    health.set_defaults(func=cmd_reliability_health)
    traces = reliability_sub.add_parser("traces")
    traces.add_argument("--json", action="store_true")
    traces.add_argument("--limit", type=int, default=80)
    traces.set_defaults(func=cmd_reliability_traces)
    log = reliability_sub.add_parser("log")
    log.add_argument("--json", action="store_true")
    log.add_argument("--limit", type=int, default=50)
    log.set_defaults(func=cmd_reliability_log)
    budget = reliability_sub.add_parser("budget")
    budget.add_argument("--json", action="store_true")
    budget.set_defaults(func=cmd_reliability_budget)


def add_morpheus_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.set_defaults(func=cmd_morpheus)


def add_daemon_parser(parser: argparse.ArgumentParser) -> None:
    daemon_sub = parser.add_subparsers(required=True)
    status = daemon_sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_daemon_status)
    run = daemon_sub.add_parser("run")
    run.add_argument("--once", action="store_true")
    run.add_argument("--interval", type=int, default=60)
    run.set_defaults(func=cmd_daemon_run)


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
    runtime_errors, runtime_warnings = validate_runtime_dependencies(workspace)
    model_errors, model_warnings = validate_models(workspace)
    skill_errors, skill_warnings = validate_skills(workspace)
    agent_errors, agent_warnings = validate_agents(workspace)
    auth_errors, auth_warnings = validate_auth(workspace)
    api_errors, api_warnings = validate_api(workspace)
    gateway_errors, gateway_warnings = validate_gateway(workspace)
    memory_errors, memory_warnings = validate_memory(workspace)
    telegram_errors, telegram_warnings = validate_telegram(workspace)
    errors.extend(runtime_errors)
    errors.extend(model_errors)
    errors.extend(skill_errors)
    errors.extend(agent_errors)
    errors.extend(auth_errors)
    errors.extend(api_errors)
    errors.extend(gateway_errors)
    errors.extend(memory_errors)
    errors.extend(telegram_errors)
    warnings.extend(runtime_warnings)
    warnings.extend(model_warnings)
    warnings.extend(skill_warnings)
    warnings.extend(agent_warnings)
    warnings.extend(auth_warnings)
    warnings.extend(gateway_warnings)
    warnings.extend(memory_warnings)
    optional_warnings = [("api", warning) for warning in api_warnings] + [
        ("telegram", warning) for warning in telegram_warnings
    ]
    if getattr(args, "advanced", False) or not is_lite(workspace.config):
        warnings.extend(api_warnings)
        warnings.extend(telegram_warnings)
    else:
        warnings.extend(
            warning
            for source, warning in optional_warnings
            if not is_optional_lite_warning(workspace.config, source, warning)
        )
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
    advanced = bool(getattr(args, "advanced", False))
    report = setup_report(workspace, advanced=advanced)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_table(setup_rows(workspace, advanced=advanced), ["step", "status", "detail", "command"])
        print()
        print_table(skill_config_rows(workspace), ["check", "status", "detail"])
    return 1 if report["status"] == "error" else 0


def cmd_mode_status(args: argparse.Namespace) -> int:
    payload = current_experience(ws())
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_table(
            [
                {
                    "mode": payload["mode"],
                    "skills": payload["skills"],
                    "enabledCount": "" if payload["enabledCount"] is None else str(payload["enabledCount"]),
                    "advancedHidden": "yes" if payload["advancedHidden"] else "no",
                }
            ],
            ["mode", "skills", "enabledCount", "advancedHidden"],
        )
    return 0


def cmd_mode_use(args: argparse.Namespace) -> int:
    payload = set_experience_mode(ws(), args.mode)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"mode={payload['mode']}")
        print(f"skills={payload['skills']}")
    return 0


def cmd_setup_wizard(args: argparse.Namespace) -> int:
    report = setup_wizard(
        ws(),
        model=args.model,
        obsidian_vault=args.obsidian_vault,
        telegram_chat_id=args.telegram_chat_id,
        telegram_token_env=args.telegram_token_env,
        enable_telegram=args.enable_telegram,
        enable_telegram_inbound=args.enable_telegram_inbound,
        interactive=not args.non_interactive,
    )
    print_table(report["steps"], ["step", "status", "detail"])
    return 0 if report["status"] in {"ok", "warning"} else 1


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


def cmd_memory_status(args: argparse.Namespace) -> int:
    status = memory_status(ws())
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print_table(
            [
                {
                    "provider": status["provider"],
                    "vaultPath": status["vaultPath"],
                    "exists": "yes" if status["vaultExists"] else "no",
                    "notes": str(status["noteCount"]),
                    "error": status["error"],
                }
            ],
            ["provider", "vaultPath", "exists", "notes", "error"],
        )
    return 1 if status.get("error") else 0


def cmd_memory_set_vault(args: argparse.Namespace) -> int:
    configure_obsidian_vault(ws(), args.path, allow_external=args.allow_external)
    print(f"memory vault {args.path}")
    return 0


def cmd_memory_record(args: argparse.Namespace) -> int:
    note = record_feedback(ws(), args.text, args.kind)
    print(note.path)
    return 0


def cmd_memory_recall(args: argparse.Namespace) -> int:
    rows = recall_memory(ws(), args.query)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["title", "score", "snippet", "path"])
    return 0


def cmd_memory_search(args: argparse.Namespace) -> int:
    rows = memory_search(
        ws(),
        args.query,
        limit=args.limit,
        note_type=args.type,
        scope=args.scope,
        min_confidence=args.min_confidence,
        tag=args.tag,
        source=args.source,
        include_expired=args.include_expired,
    )
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["title", "kind", "type", "confidence", "score", "snippet", "path"])
    return 0


def cmd_memory_write_note(args: argparse.Namespace) -> int:
    note = memory_write_note(
        ws(),
        args.title,
        args.body,
        kind=args.kind,
        note_type=args.type,
        tags=args.tag,
        links=args.link,
        confidence=args.confidence,
        sources=args.source,
        ttl_days=args.ttl_days,
        scope=parse_scope_args(args.scope),
        author=args.author,
        agent=args.agent,
        reason=args.reason,
        blame=args.blame,
        expected_version=args.expected_version,
        append=args.append,
    )
    print(note.path)
    return 0


def parse_scope_args(values: list[str]) -> dict[str, str]:
    scope: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"scope must be key=value: {value}")
        key, raw = value.split("=", 1)
        key = key.strip()
        if key not in {"user", "project", "machine", "channel", "thread", "profile"}:
            raise ValueError(f"unsupported scope key: {key}")
        scope[key] = raw.strip()
    return scope


def cmd_memory_get_note(args: argparse.Namespace) -> int:
    note = memory_get_note(ws(), args.title)
    if args.json:
        print(json.dumps(note, indent=2, ensure_ascii=False))
    else:
        print(note["raw"])
    return 0


def cmd_memory_link(args: argparse.Namespace) -> int:
    note = memory_link(ws(), args.from_title, args.to_title)
    print(note.path)
    return 0


def cmd_ledger_summary(args: argparse.Namespace) -> int:
    summary = ledger_summary(ws())
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        totals = summary["totals"]
        print_table(
            [
                {
                    "runs": str(totals["runs"]),
                    "estimatedTokens": str(totals["estimatedTokens"]),
                    "providerTokens": str(totals["providerTotalTokens"]),
                    "costUsd": f"{float(totals['costUsd']):.6f}",
                    "path": summary["path"],
                }
            ],
            ["runs", "estimatedTokens", "providerTokens", "costUsd", "path"],
        )
    return 0


def cmd_ledger_list(args: argparse.Namespace) -> int:
    rows = ledger_rows(ws(), args.limit)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["timestamp", "runId", "agent", "status", "model", "estimatedTokens", "providerTokens", "costUsd"])
    return 0


def cmd_telegram_status(args: argparse.Namespace) -> int:
    status = telegram_status(ws())
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print_table(
            [
                {
                    "enabled": "yes" if status["enabled"] else "no",
                    "botTokenEnv": status["botTokenEnv"],
                    "tokenPresent": "yes" if status["tokenPresent"] else "no",
                    "chatId": "set" if status["chatId"] else "",
                    "parseMode": status["parseMode"],
                    "inbound": "yes" if status["inboundEnabled"] else "no",
                }
            ],
            ["enabled", "botTokenEnv", "tokenPresent", "chatId", "parseMode", "inbound"],
        )
    return 0


def cmd_telegram_setup(args: argparse.Namespace) -> int:
    configure_telegram(ws(), args.chat_id, args.token_env, enabled=args.enable, inbound_enabled=args.enable_inbound)
    print(f"telegram chat id {'enabled' if args.enable else 'configured'}")
    return 0


def cmd_telegram_test(args: argparse.Namespace) -> int:
    result = send_telegram_message(ws(), args.message)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["stdout"]:
            print(result["stdout"])
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr)
    return int(result.get("returncode") or 0)


def cmd_telegram_poll(args: argparse.Namespace) -> int:
    from .telegram import poll_telegram_once

    result = poll_telegram_once(ws())
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_table(result.get("messages", []), ["updateId", "chatId", "text", "memoryNote"])
    return 0


def cmd_approvals_list(args: argparse.Namespace) -> int:
    rows = approval_rows(ws())
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["id", "category", "riskTier", "title", "origin", "status", "resources", "dryRun", "rollback"])
    return 0


def cmd_approvals_approve(args: argparse.Namespace) -> int:
    result = approve(ws(), args.id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("result") or "approved")
    return 0


def cmd_approvals_reject(args: argparse.Namespace) -> int:
    result = reject(ws(), args.id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("result") or "rejected")
    return 0


def cmd_learning_list(args: argparse.Namespace) -> int:
    rows = learning_proposal_rows(ws())
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["id", "targetType", "target", "action", "riskTier", "confidence", "evidence", "reason"])
    return 0


def cmd_learning_events(args: argparse.Namespace) -> int:
    rows = learning_event_rows(ws(), limit=args.limit)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["timestamp", "status", "action", "targetType", "target", "confidence", "evidenceStrength", "reason"])
    return 0


def cmd_learning_show(args: argparse.Namespace) -> int:
    print(json.dumps(show_learning_proposal(ws(), args.id), indent=2, ensure_ascii=False))
    return 0


def cmd_learning_approve(args: argparse.Namespace) -> int:
    result = approve_learning(ws(), args.id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("result") or "approved")
    return 0


def cmd_learning_reject(args: argparse.Namespace) -> int:
    result = reject_learning(ws(), args.id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("result") or "rejected")
    return 0


def cmd_learning_rollback(args: argparse.Namespace) -> int:
    result = rollback_learning(ws(), args.event_id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("result") or "rolled back")
    return 0


def cmd_reliability_health(args: argparse.Namespace) -> int:
    rows = health_checks(ws())
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["name", "status", "detail"])
    return 1 if any(row["status"] == "error" for row in rows) else 0


def cmd_reliability_traces(args: argparse.Namespace) -> int:
    rows = trace_rows(ws(), limit=args.limit)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["timestamp", "traceId", "stage", "status", "resource", "message"])
    return 0


def cmd_reliability_log(args: argparse.Namespace) -> int:
    rows = reliability_rows(ws(), limit=args.limit)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["timestamp", "traceId", "stage", "status", "resource", "message"])
    return 0


def cmd_reliability_budget(args: argparse.Namespace) -> int:
    payload = budget_status(ws())
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_table(
            [
                {"window": "per-run", **{key: str(value) for key, value in payload["perRun"].items()}},
                {"window": "daily", **{key: str(value) for key, value in payload["daily"].items()}},
                {"window": "monthly", **{key: str(value) for key, value in payload["monthly"].items()}},
            ],
            ["window", "used", "limit"],
        )
    return 0


def cmd_morpheus(args: argparse.Namespace) -> int:
    result = run_morpheus(ws(), dry_run=args.dry_run)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["summary"])
        print(f"record {result['record']}")
    return 0


def cmd_daemon_status(args: argparse.Namespace) -> int:
    workspace = ws()
    payload = {"daemon": daemon_status(workspace), "schedules": schedule_rows(workspace)}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_table([payload["daemon"]], ["running", "lastCheck", "lastMorpheus", "path"])
        print()
        print_table(payload["schedules"], ["id", "name", "hour", "minute", "action", "created"])
    return 0


def cmd_daemon_run(args: argparse.Namespace) -> int:
    run_daemon(ws(), once=args.once, interval_seconds=args.interval)
    return 0


def cmd_skills_list(args: argparse.Namespace) -> int:
    workspace = ws()
    ensure_bundled_skills(workspace)
    rows = skill_rows(workspace)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["name", "enabled", "source", "description", "reason"])
    return 0


def cmd_skills_show(args: argparse.Namespace) -> int:
    workspace = ws()
    ensure_bundled_skills(workspace)
    for skill in discover_skills(workspace):
        if skill.name == args.name:
            print(skill.path.read_text(encoding="utf-8"))
            return 0
    print(f"skill not found: {args.name}", file=sys.stderr)
    return 1


def cmd_skills_validate(args: argparse.Namespace) -> int:
    workspace = ws()
    ensure_bundled_skills(workspace)
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
    workspace = ws()
    ensure_bundled_skills(workspace)
    rows = skill_config_rows(workspace)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["check", "status", "detail"])
    return 1 if any(row["status"] == "error" for row in rows) else 0


def cmd_skills_safety(args: argparse.Namespace) -> int:
    workspace = ws()
    ensure_bundled_skills(workspace)
    rows = skill_safety_rows(workspace)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows, ["name", "version", "author", "source", "hash", "immutable", "lastVerified", "permissions"])
    return 0


def cmd_skills_create(args: argparse.Namespace) -> int:
    path = create_skill(ws(), args.name, args.description, args.group)
    print(path)
    return 0


def cmd_skills_sync(args: argparse.Namespace) -> int:
    workspace = ws()
    ensure_bundled_skills(workspace)
    config = {row["check"]: row for row in skill_config_rows(workspace)}
    payload = {
        "status": "ok",
        "mode": "repo-managed",
        "source": args.source,
        "dryRun": True,
        "detail": "Exact Hermes/OpenClaw mirrors are kept in this repository; sync is a non-mutating status check.",
        "hotReload": "Skill discovery keys include SKILL.md mtimes and enabled/disabled selection.",
        "eligibility": "Only enabled and eligible skills are injected into packets; gated skills remain inspectable.",
        "upstreamMirror": config.get("upstream-mirror", {}),
        "reflections": config.get("reflections", {}),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_table(
            [
                {
                    "status": payload["status"],
                    "mode": payload["mode"],
                    "source": payload["source"] or "repo mirrors",
                    "upstreamMirror": str(payload["upstreamMirror"].get("detail") or ""),
                    "hotReload": "mtime cache",
                    "eligibility": "enabled+eligible",
                }
            ],
            ["status", "mode", "source", "upstreamMirror", "hotReload", "eligibility"],
        )
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
    if args.format == "prompt":
        print(packet["prompt"])
    elif args.format == "summary":
        print_packet_summary(packet)
    else:
        print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


def print_packet_summary(packet: dict[str, Any]) -> None:
    prompt = str(packet.get("prompt") or "")
    print_table(
        [
            {
                "agent": str((packet.get("agent") or {}).get("id") or ""),
                "model": str((packet.get("model") or {}).get("id") or ""),
                "runner": str((packet.get("agent") or {}).get("runner") or ""),
                "style": str(packet.get("promptStyle") or ""),
                "sections": ",".join(str(item) for item in packet.get("promptSections") or []),
                "skills": str(len(packet.get("skills") or [])),
                "memory": str(len(packet.get("memory") or [])),
                "estimatedTokens": str(max(1, (len(prompt) + 3) // 4) if prompt else 0),
                "promptChars": str(len(prompt)),
            }
        ],
        ["agent", "model", "runner", "style", "sections", "skills", "memory", "estimatedTokens", "promptChars"],
    )


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
    execute = False if args.dry_run else args.execute
    payload = run_chat(
        ws(),
        args.message,
        agent_id=args.agent,
        model_name=args.model,
        provider_name=args.provider,
        execute=execute,
    )
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload["reply"])
        print(f"record {payload['record']}")
    return 0 if payload["status"] in {"ok", "packet-only"} else 1


def startup_model_label(workspace: Workspace, model_name: str | None) -> str:
    selected = (model_name or default_model_id(workspace)).strip() or "packet"
    profile = model_profile_map(workspace).get(selected)
    if not profile:
        return selected
    provider = profile.provider.lower()
    if "codex" in provider:
        return "codex"
    if "claude" in provider:
        return "claude"
    if profile.model and profile.model != "packet-only":
        return profile.model
    return profile.id


def startup_skill_count(workspace: Workspace) -> int:
    try:
        ensure_bundled_skills(workspace)
        return sum(1 for record in discover_skills(workspace) if record.enabled and record.eligible)
    except Exception:
        enabled = current_experience(workspace).get("enabledCount")
        return int(enabled) if isinstance(enabled, int) else 0


def startup_banner(workspace: Workspace, model_name: str | None = None) -> str:
    memory = memory_status(workspace)
    vault = str(memory.get("vaultPath") or "")
    model = startup_model_label(workspace, model_name)
    skill_count = startup_skill_count(workspace)
    return "\n".join(
        [
            BIRKIN_STARTUP_ART,
            "The AI agent that actually remembers you.",
            "",
            f"model {model} · {skill_count} skill(s) · vault {vault}",
            "type /help for commands, or just chat · Ctrl-C to quit.",
        ]
    )


def slash_command_rows(prefix: str = "") -> list[dict[str, str]]:
    needle = prefix.strip().lower()
    if needle in {"", "/"}:
        return list(SLASH_COMMANDS)
    return [
        row
        for row in SLASH_COMMANDS
        if row["command"].startswith(needle) or row["usage"].startswith(needle)
    ]


def print_slash_commands(prefix: str = "") -> None:
    rows = slash_command_rows(prefix)
    if not rows:
        print(f"unknown command: {prefix}")
        rows = list(SLASH_COMMANDS)
    print_table(rows, ["command", "usage", "description"])


def install_slash_completion() -> None:
    try:
        import readline  # type: ignore[import-not-found]
    except Exception:
        return
    commands = [row["command"] for row in SLASH_COMMANDS if row["command"] != "/"]

    def complete(text: str, state: int) -> str | None:
        if not text.startswith("/"):
            return None
        matches = [command for command in commands if command.startswith(text)]
        try:
            return matches[state]
        except IndexError:
            return None

    try:
        readline.set_completer(complete)
        readline.parse_and_bind("tab: complete")
    except Exception:
        return


def print_chat_status(
    workspace: Workspace,
    agent_id: str | None,
    model_name: str | None,
    execute: bool,
) -> None:
    memory = memory_status(workspace)
    rows = [
        {
            "agent": agent_id or "chat",
            "model": startup_model_label(workspace, model_name),
            "mode": str(current_experience(workspace)["mode"]),
            "skills": str(startup_skill_count(workspace)),
            "execute": "on" if execute else "off",
            "vault": str(memory.get("vaultPath") or ""),
        }
    ]
    print_table(rows, ["agent", "model", "mode", "skills", "execute", "vault"])


def cmd_chat_interactive(args: argparse.Namespace) -> int:
    workspace = ws()
    ensure_bundled_skills(workspace)
    agent_id = args.agent
    model_name = args.model
    provider_name = args.provider
    execute = bool(args.execute) and not bool(getattr(args, "dry_run", False))
    history: list[dict[str, str]] = []

    install_slash_completion()
    print(startup_banner(workspace, model_name))
    print()
    print_chat_status(workspace, agent_id, model_name, execute)

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
        if lowered in {"/", "/?", "/help", "/commands"}:
            print_slash_commands()
            continue
        if lowered == "/status":
            print_chat_status(workspace, agent_id, model_name, execute)
            continue
        if lowered == "/live":
            selected, detail = choose_live_model(workspace)
            if not selected:
                print(detail)
                continue
            model_name = selected
            execute = True
            print(f"live mode on: model={model_name} execute=on")
            print(detail)
            continue
        if lowered == "/setup":
            print_table(setup_rows(workspace), ["step", "status", "detail", "command"])
            continue
        if lowered == "/dashboard":
            print("Run: birkin-codex web --port 8765")
            print("Then open: http://127.0.0.1:8765")
            continue
        if lowered == "/skills":
            ensure_bundled_skills(workspace)
            print_table(skill_config_rows(workspace), ["check", "status", "detail"])
            continue
        if lowered.startswith("/mode "):
            value = message.split(maxsplit=1)[1].strip().lower()
            if value not in {"lite", "full"}:
                print("usage: /mode lite|full")
                print_slash_commands("/mode")
                continue
            payload = set_experience_mode(workspace, value)
            ensure_bundled_skills(workspace)
            print(f"mode={payload['mode']} skills={payload['skills']}")
            continue
        if lowered.startswith("/model "):
            model_name = message.split(maxsplit=1)[1].strip()
            print(f"model={model_name}")
            continue
        if lowered.startswith("/execute "):
            value = message.split(maxsplit=1)[1].strip().lower()
            if value not in {"on", "off"}:
                print("usage: /execute on|off")
                print_slash_commands("/execute")
                continue
            execute = value == "on"
            print(f"execute={'on' if execute else 'off'}")
            continue
        if lowered.startswith("/"):
            print_slash_commands(lowered)
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


def choose_live_model(workspace: Workspace) -> tuple[str | None, str]:
    profiles = model_profile_map(workspace)
    if "api-agent" in profiles and os.getenv("OPENAI_API_KEY"):
        return "api-agent", "Using OpenAI-compatible tool-agent profile from OPENAI_API_KEY."
    if "codex-local" in profiles and shutil.which("codex"):
        return "codex-local", "Using local Codex CLI profile. OAuth/login stays in the Codex CLI."
    for profile_id, profile in profiles.items():
        if profile_id in {"api-agent", "codex-local"}:
            continue
        if profile.runner == "local-cli" and profile.command and shutil.which(profile.command[0]):
            return profile_id, f"Using configured live profile {profile_id} ({profile.runner})."
        if profile.runner in {"api", "tool-agent"} and os.getenv("OPENAI_API_KEY"):
            return profile_id, f"Using configured live profile {profile_id} ({profile.runner})."
    return (
        None,
        "Live mode needs a configured runner. Run `birkin-codex setup wizard`, "
        "`birkin-codex auth login codex-cli`, or set OPENAI_API_KEY for `api-agent`.",
    )
