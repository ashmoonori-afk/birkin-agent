from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from birkin_agent.agents import build_packet, run_agent, validate_agents
from birkin_agent.api import api_rows, validate_api
from birkin_agent.approvals import approval_rows, propose_action
from birkin_agent.auth import auth_rows, run_auth_command, validate_auth
from birkin_agent.chat import run_chat
from birkin_agent.cli import main as cli_main
from birkin_agent.dashboard import dashboard_data
from birkin_agent.gateway import GatewayHandler
from birkin_agent.improve import append_lesson, apply_improvement, propose_improvement
from birkin_agent.learning import (
    add_learning_proposal,
    approve_learning,
    learning_event_rows,
    learning_proposal_rows,
    rollback_learning,
)
from birkin_agent.ledger import ledger_rows, ledger_summary
from birkin_agent.memory import (
    memory_get_note,
    memory_link,
    memory_search,
    memory_status,
    memory_write_note,
    recall_memory,
    record_feedback,
)
from birkin_agent.models import render_model_command, resolve_model_profile, use_model_profile, validate_models
from birkin_agent.morpheus import run_morpheus
from birkin_agent.reliability import budget_status, health_checks, reliability_rows, trace_rows
from birkin_agent.runtime import memory_write_tool
from birkin_agent.setup import setup_report
from birkin_agent.skills import create_skill, discover_skills, immutable_skill, skill_config_rows, skill_safety_rows, validate_skills
from birkin_agent.telegram import configure_telegram, telegram_status, validate_telegram
from birkin_agent.web import Handler
from birkin_agent.wizard import setup_wizard
from birkin_agent.workspace import Workspace


class WorkspaceTest(unittest.TestCase):
    def make_workspace(self) -> Workspace:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workspace = Workspace(Path(tmp.name))
        workspace.init()
        source_skills = Path(__file__).resolve().parents[1] / "skills"
        shutil.copytree(source_skills, workspace.root / "skills", dirs_exist_ok=True)
        return workspace

    def test_init_and_validate_default_skills(self) -> None:
        workspace = self.make_workspace()
        errors, warnings = validate_skills(workspace)
        self.assertEqual(errors, [])
        self.assertIsInstance(warnings, list)
        names = {skill.name for skill in discover_skills(workspace)}
        self.assertIn("self-improvement", names)
        self.assertIn("taskflow", names)
        openclaw_names = {name for name in names if name.startswith("openclaw-")}
        self.assertGreaterEqual(len(openclaw_names), 57)
        self.assertIn("openclaw-github", openclaw_names)
        hermes_names = {name for name in names if name.startswith("hermes-")}
        self.assertGreaterEqual(len(hermes_names), 90)
        self.assertIn("hermes-test-driven-development", hermes_names)
        self.assertIn("hermes-ascii-art", hermes_names)
        self.assertIn("chat", {raw["id"] for raw in workspace.config["agents"]["list"]})
        self.assertTrue((workspace.root / "scripts" / "birkin-codex").exists())
        self.assertTrue((workspace.root / "scripts" / "birkin-codex.ps1").exists())
        self.assertTrue((workspace.root / "scripts" / "birkin").exists())
        self.assertTrue((workspace.root / "scripts" / "birkin.ps1").exists())
        self.assertTrue((workspace.root / "scripts" / "setup").exists())
        self.assertTrue((workspace.root / "scripts" / "setup.ps1").exists())

    def test_agent_packet_uses_final_skill_allowlist(self) -> None:
        workspace = self.make_workspace()
        packet = build_packet(workspace, "planner", "Plan a release")
        names = {skill["name"] for skill in packet["skills"]}
        self.assertEqual(names, {"taskflow", "memory-recall", "documentation"})
        self.assertEqual(packet["model"]["id"], "packet")
        self.assertEqual(packet["model"]["runner"], "dry-run")
        self.assertIn("<available_skills>", packet["prompt"])
        self.assertNotIn("shell-runtime", names)

    def test_model_profiles_select_local_cli_templates(self) -> None:
        workspace = self.make_workspace()
        errors, warnings = validate_models(workspace)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        profile = resolve_model_profile(workspace, "codex-local")
        self.assertEqual(profile.runner, "local-cli")
        self.assertEqual(resolve_model_profile(workspace, "api-openai").api_profile, "openai-compatible")
        self.assertEqual(
            render_model_command(profile.command, profile),
            ["codex", "exec", "--model", "gpt-5.5", "-"],
        )
        use_model_profile(workspace, "codex-local")
        packet = build_packet(workspace, "builder", "Build a feature")
        self.assertEqual(packet["model"]["id"], "codex-local")
        self.assertEqual(packet["agent"]["runner"], "local-cli")

    def test_model_profile_executes_local_cli_command(self) -> None:
        workspace = self.make_workspace()
        workspace.config["models"]["profiles"]["test-local"] = {
            "provider": "test-cli",
            "model": "unit-model",
            "runner": "local-cli",
            "command": [
                sys.executable,
                "-c",
                "import sys; data=sys.stdin.read(); print('model-output:' + str(len(data)))",
            ],
            "timeoutSeconds": 30,
            "description": "Unit-test local CLI model.",
        }
        workspace.save_config()
        record, result = run_agent(
            workspace,
            "planner",
            "Plan a release",
            model_name="test-local",
            execute=True,
        )
        self.assertEqual(result["returncode"], 0)
        self.assertIn("model-output:", result["stdout"])
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["model"]["id"], "test-local")

    def test_auth_profiles_delegate_to_local_cli_commands(self) -> None:
        workspace = self.make_workspace()
        workspace.config["auth"]["profiles"]["unit-auth"] = {
            "type": "local-cli-oauth",
            "provider": "unit-cli",
            "binary": sys.executable,
            "loginCommand": [sys.executable, "-c", "print('login-ok')"],
            "logoutCommand": [sys.executable, "-c", "print('logout-ok')"],
            "statusCommand": [sys.executable, "-c", "print('status-ok')"],
            "required": True,
            "description": "Unit-test CLI auth profile.",
        }
        workspace.save_config()
        errors, warnings = validate_auth(workspace)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        result = run_auth_command(workspace, "unit-auth", "status")
        self.assertEqual(result["returncode"], 0)
        self.assertIn("status-ok", result["stdout"])
        rows = {row["id"]: row for row in auth_rows(workspace)}
        self.assertEqual(rows["unit-auth"]["available"], "yes")

    def test_api_runner_uses_openai_compatible_profile(self) -> None:
        workspace = self.make_workspace()

        class ApiHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def do_POST(self) -> None:
                length = int(self.headers.get("content-length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                body = json.dumps(
                    {"choices": [{"message": {"content": "api-output:" + payload["model"]}}]}
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        host, port = server.server_address

        workspace.config["api"]["profiles"]["unit-api"] = {
            "type": "openai-compatible",
            "baseUrl": f"http://{host}:{port}/v1",
            "apiKeyEnv": "",
            "chatPath": "/chat/completions",
            "timeoutSeconds": 30,
            "description": "Unit-test API profile.",
        }
        workspace.config["models"]["profiles"]["unit-api"] = {
            "provider": "unit-api",
            "model": "unit-model",
            "runner": "api",
            "apiProfile": "unit-api",
            "command": [],
            "timeoutSeconds": 30,
            "description": "Unit-test API model.",
        }
        workspace.save_config()
        errors, _warnings = validate_api(workspace)
        self.assertEqual(errors, [])
        rows = {row["id"]: row for row in api_rows(workspace)}
        self.assertEqual(rows["unit-api"]["baseUrl"], f"http://{host}:{port}/v1")

        record, result = run_agent(
            workspace,
            "planner",
            "Plan a release",
            model_name="unit-api",
            execute=True,
        )
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "api-output:unit-model")
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["result"]["apiProfile"], "unit-api")

    def test_tool_agent_runtime_executes_memory_tool(self) -> None:
        workspace = self.make_workspace()

        class ToolApiHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def do_POST(self) -> None:
                length = int(self.headers.get("content-length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                has_tool_result = any(message.get("role") == "tool" for message in payload["messages"])
                if has_tool_result:
                    body = {
                        "choices": [{"message": {"role": "assistant", "content": "memory saved"}}],
                        "usage": {"total_tokens": 8},
                    }
                else:
                    body = {
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [
                                        {
                                            "id": "call_1",
                                            "type": "function",
                                            "function": {
                                                "name": "memory_write_note",
                                                "arguments": json.dumps(
                                                    {
                                                        "title": "Runtime Memory",
                                                        "body": "The tool agent can write semantic memory.",
                                                        "kind": "feedback",
                                                        "type": "fact",
                                                        "tags": ["runtime"],
                                                        "sources": ["unit-test"],
                                                        "links": ["Tool Agent"],
                                                    }
                                                ),
                                            },
                                        }
                                    ],
                                }
                            }
                        ],
                        "usage": {"prompt_tokens": 5},
                    }
                encoded = json.dumps(body).encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        server = ThreadingHTTPServer(("127.0.0.1", 0), ToolApiHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        host, port = server.server_address

        workspace.config["api"]["profiles"]["unit-tool-api"] = {
            "type": "openai-compatible",
            "baseUrl": f"http://{host}:{port}/v1",
            "apiKeyEnv": "",
            "chatPath": "/chat/completions",
            "timeoutSeconds": 30,
            "description": "Unit-test tool API profile.",
        }
        workspace.config["models"]["profiles"]["unit-tool-agent"] = {
            "provider": "unit-api",
            "model": "unit-model",
            "runner": "tool-agent",
            "apiProfile": "unit-tool-api",
            "command": [],
            "timeoutSeconds": 30,
            "description": "Unit-test tool agent model.",
        }
        workspace.save_config()
        record, result = run_agent(
            workspace,
            "planner",
            "Write a memory note through a tool.",
            model_name="unit-tool-agent",
            execute=True,
        )
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "memory saved")
        self.assertEqual(result["toolCalls"][0]["name"], "memory_write_note")
        self.assertTrue(memory_search(workspace, "Runtime Memory"))
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["runner"], "tool-agent")

    def test_hermes_reflections_keep_source_metadata(self) -> None:
        workspace = self.make_workspace()
        records = {skill.name: skill for skill in discover_skills(workspace)}
        tdd = records["hermes-test-driven-development"]
        hermes = tdd.frontmatter["metadata"]["hermes"]
        self.assertEqual(hermes["upstreamSkill"], "test-driven-development")
        self.assertEqual(
            hermes["upstreamPath"],
            "skills/software-development/test-driven-development",
        )
        self.assertEqual(hermes["category"], "software-development")

    def test_run_agent_dry_run_writes_record(self) -> None:
        workspace = self.make_workspace()
        record, result = run_agent(workspace, "planner", "Plan a release")
        self.assertTrue(record.exists())
        self.assertFalse(result["executed"])
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "packet-only")
        self.assertEqual(payload["model"]["id"], "packet")
        self.assertIn("summary", payload)
        self.assertGreater(payload["usage"]["estimatedTokens"], 0)

    def test_setup_and_skill_config_report(self) -> None:
        workspace = self.make_workspace()
        report = setup_report(workspace)
        self.assertIn(report["status"], {"ok", "warning"})
        checks = {row["step"]: row for row in report["checks"]}
        self.assertIn("workspace", checks)
        self.assertIn("chat", checks)
        config = {row["check"]: row for row in skill_config_rows(workspace)}
        self.assertEqual(config["catalog"]["status"], "ok")
        self.assertIn("90 Hermes", config["reflections"]["detail"])
        self.assertEqual(config["upstream-mirror"]["status"], "ok")
        self.assertIn("147 mirrored", config["upstream-mirror"]["detail"])

    def test_chat_packet_writes_record(self) -> None:
        workspace = self.make_workspace()
        payload = run_chat(workspace, "Hello from chat", model_name="packet")
        self.assertEqual(payload["agent"], "chat")
        self.assertEqual(payload["status"], "packet-only")
        self.assertIn("Prompt packet built", payload["reply"])
        self.assertTrue(Path(payload["record"]).exists())
        self.assertIn("memoryNote", payload)
        self.assertTrue(Path(payload["memoryNote"]).exists())
        self.assertGreaterEqual(ledger_summary(workspace)["totals"]["runs"], 1)

    def test_cli_without_args_opens_interactive_chat(self) -> None:
        workspace = self.make_workspace()
        with (
            patch("birkin_agent.cli.ws", return_value=workspace),
            patch("builtins.input", side_effect=["/exit"]),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            self.assertEqual(cli_main([]), 0)
        output = stdout.getvalue()
        self.assertIn("Birkin Codex", output)
        self.assertIn("Commands: /help", output)
        self.assertIn("bye", output)

    def test_obsidian_memory_recall_and_ledger(self) -> None:
        workspace = self.make_workspace()
        note = record_feedback(workspace, "USER_CORRECTION: prefer Obsidian memory for feedback.")
        self.assertTrue(note.path.exists())
        recalled = recall_memory(workspace, "Obsidian feedback")
        self.assertTrue(recalled)
        status = memory_status(workspace)
        self.assertTrue(status["vaultExists"])
        run_agent(workspace, "planner", "Plan with ledger")
        rows = ledger_rows(workspace)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["agent"], "planner")

    def test_semantic_memory_write_get_link_search(self) -> None:
        workspace = self.make_workspace()
        first = memory_write_note(
            workspace,
            "Model Preference",
            "Prefer local CLI model selection unless an API run is explicitly requested.",
            kind="feedback",
            note_type="preference",
            tags=["models"],
            sources=["unit-test"],
            confidence=0.9,
        )
        self.assertTrue(first.path.exists())
        memory_write_note(
            workspace,
            "API Gateway",
            "Gateway actions should stay localhost or token-gated.",
            kind="feedback",
            note_type="fact",
            tags=["gateway"],
            sources=["unit-test"],
        )
        linked = memory_link(workspace, "Model Preference", "API Gateway")
        raw = linked.path.read_text(encoding="utf-8")
        self.assertIn("[[API Gateway]]", raw)
        note = memory_get_note(workspace, "Model Preference")
        self.assertEqual(note["type"], "preference")
        self.assertEqual(note["kind"], "feedback")
        found = memory_search(workspace, "API Gateway")
        self.assertTrue(found)

    def test_memory_os_metadata_filters_version_and_history(self) -> None:
        workspace = self.make_workspace()
        first = memory_write_note(
            workspace,
            "Scoped Negative Memory",
            "Playwright failed because the binary was unavailable in this environment.",
            kind="negative",
            note_type="negative",
            tags=["playwright"],
            sources=["run:unit-run-1"],
            evidence=[{"type": "run", "ref": "runs/unit-run-1.json"}],
            confidence=0.91,
            ttl_days=7,
            scope={"project": "unit", "machine": "windows", "profile": "tester"},
            agent="unit-test",
            reason="verify typed scoped memory",
        )
        self.assertTrue(first.path.exists())
        note = memory_get_note(workspace, "Scoped Negative Memory")
        self.assertEqual(note["type"], "negative")
        self.assertEqual(note["kind"], "negative")
        self.assertEqual(note["version"], "1")
        self.assertIn('"project": "unit"', note["scope"])
        self.assertIn("runs/unit-run-1.json", note["evidence"])
        filtered = memory_search(
            workspace,
            "Playwright",
            note_type="negative",
            scope="windows",
            min_confidence=0.9,
            tag="playwright",
            source="unit-run-1",
        )
        self.assertTrue(filtered)
        second = memory_write_note(
            workspace,
            "Scoped Negative Memory",
            "Revalidate before preserving this negative memory.",
            kind="negative",
            note_type="negative",
            evidence=[{"type": "test", "ref": "tests/test_birkin.py"}],
            expected_version=1,
            append=True,
        )
        self.assertTrue(second.path.exists())
        self.assertEqual(memory_get_note(workspace, "Scoped Negative Memory")["version"], "2")
        self.assertTrue((workspace.root / "memory" / "history.jsonl").exists())
        self.assertTrue(learning_event_rows(workspace))

    def test_learning_proposal_approval_and_rollback(self) -> None:
        workspace = self.make_workspace()
        proposal = add_learning_proposal(
            workspace,
            target_type="memory",
            target="Approved Memory",
            action="memory-write",
            before="",
            after="Approved through verified learning.",
            evidence=[{"type": "feedback", "ref": "manual"}],
            confidence=0.92,
            reason="unit-test proposal",
            apply_payload={
                "kind": "memory-note",
                "title": "Approved Memory",
                "body": "Approved through verified learning.",
                "memoryKind": "feedback",
                "noteType": "feedback",
                "tags": ["learning"],
            },
        )
        self.assertEqual(len(learning_proposal_rows(workspace)), 1)
        result = approve_learning(workspace, proposal.id)
        self.assertEqual(result["status"], "approved")
        self.assertIn("Approved through verified learning", memory_get_note(workspace, "Approved Memory")["body"])
        events = learning_event_rows(workspace)
        self.assertTrue(events)
        memory_write_event = next(row for row in events if row["action"] == "memory-write")
        rollback = rollback_learning(workspace, memory_write_event["id"])
        self.assertIn("removed", rollback["result"])

    def test_tool_memory_overwrite_becomes_learning_proposal(self) -> None:
        workspace = self.make_workspace()
        memory_write_note(
            workspace,
            "Manual Memory",
            "This note was written manually.",
            kind="feedback",
            note_type="feedback",
            author="user",
            evidence=[{"type": "feedback", "ref": "manual"}],
        )
        result = memory_write_tool(
            workspace,
            {
                "title": "Manual Memory",
                "body": "A tool-agent wants to replace it.",
                "kind": "feedback",
                "type": "feedback",
                "sources": ["run:tool-agent"],
            },
        )
        self.assertIn("queued learning proposal", result.content)
        self.assertEqual(memory_get_note(workspace, "Manual Memory")["body"], "This note was written manually.")
        self.assertEqual(len(learning_proposal_rows(workspace)), 1)

    def test_approvals_queue_and_resolve_file_write(self) -> None:
        workspace = self.make_workspace()
        proposed = propose_action(
            workspace,
            category="file",
            title="Write approval smoke file",
            description="Create a small file only after approval.",
            payload={"path": "approved/smoke.txt", "content": "approved"},
            origin="unit-test",
        )
        self.assertEqual(proposed["status"], "pending")
        rows = approval_rows(workspace)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["riskTier"], "review")
        self.assertIn("approved/smoke.txt", rows[0]["resources"])
        self.assertIn("write approved/smoke.txt", rows[0]["dryRun"])
        from birkin_agent.approvals import approve

        result = approve(workspace, rows[0]["id"])
        self.assertIn("wrote approved", result["result"])
        self.assertEqual((workspace.root / "approved" / "smoke.txt").read_text(encoding="utf-8"), "approved")
        self.assertEqual(approval_rows(workspace), [])
        self.assertTrue(reliability_rows(workspace))

    def test_morpheus_dry_run_no_key(self) -> None:
        workspace = self.make_workspace()
        result = run_morpheus(workspace, dry_run=True)
        self.assertEqual(result["status"], "dry-run")
        self.assertTrue(Path(result["record"]).exists())
        self.assertIn("recent runs", result["summary"])

    def test_morpheus_weak_learning_becomes_proposal(self) -> None:
        workspace = self.make_workspace()
        append_lesson(workspace, "LESSON: remember weak signals as proposals.", "morpheus-lessons")
        result = run_morpheus(workspace, dry_run=False)
        self.assertEqual(result["status"], "ok")
        proposals = learning_proposal_rows(workspace)
        self.assertTrue(proposals)
        self.assertTrue(any(row["targetType"] in {"memory", "skill"} for row in proposals))

    def test_setup_wizard_model_memory_and_telegram(self) -> None:
        workspace = self.make_workspace()
        report = setup_wizard(
            workspace,
            model="packet",
            obsidian_vault="memory/test-vault",
            telegram_chat_id="12345",
            telegram_token_env="BIRKIN_TEST_TELEGRAM_TOKEN",
            enable_telegram=True,
            interactive=False,
        )
        self.assertIn(report["status"], {"ok", "warning"})
        self.assertEqual(workspace.config["models"]["default"], "packet")
        self.assertIn("test-vault", memory_status(workspace)["vaultPath"])
        status = telegram_status(workspace)
        self.assertTrue(status["enabled"])
        self.assertEqual(status["chatId"], "12345")

    def test_telegram_inbound_config_is_env_only(self) -> None:
        workspace = self.make_workspace()
        configure_telegram(
            workspace,
            "",
            "BIRKIN_TEST_TELEGRAM_TOKEN",
            enabled=False,
            inbound_enabled=True,
        )
        status = telegram_status(workspace)
        self.assertTrue(status["inboundEnabled"])
        self.assertEqual(status["botTokenEnv"], "BIRKIN_TEST_TELEGRAM_TOKEN")
        errors, warnings = validate_telegram(workspace)
        self.assertIn("telegram bot token environment variable is not set: BIRKIN_TEST_TELEGRAM_TOKEN", errors)
        self.assertEqual(warnings, [])

    def test_dashboard_summarizes_jobs_usage_and_warnings(self) -> None:
        workspace = self.make_workspace()
        run_agent(workspace, "planner", "Plan a release")
        data = dashboard_data(workspace)
        self.assertGreaterEqual(data["metrics"]["completedJobs"], 1)
        self.assertGreaterEqual(data["usage"]["estimatedTokens"], 1)
        self.assertIn("jobs", data)
        self.assertIn("warnings", data)
        self.assertIn("summary", data)
        self.assertIn("models", data)
        self.assertIn("auth", data)
        self.assertIn("api", data)
        self.assertIn("gateway", data)
        self.assertIn("memory", data)
        self.assertIn("telegram", data)
        self.assertIn("ledger", data)
        self.assertIn("ledgerRows", data)
        self.assertIn("setup", data)
        self.assertIn("skillConfig", data)
        self.assertIn("learningProposals", data)
        self.assertIn("learningEvents", data)
        self.assertIn("reliability", data)
        self.assertIn("traces", data)
        self.assertIn("health", data)
        self.assertIn("budget", data)
        self.assertIn("skillSafety", data)
        self.assertGreaterEqual(data["metrics"]["modelsTotal"], 4)
        self.assertGreaterEqual(data["metrics"]["authProfiles"], 2)
        self.assertGreaterEqual(data["metrics"]["apiProfiles"], 2)
        self.assertTrue(trace_rows(workspace))
        self.assertTrue(health_checks(workspace))
        self.assertIn("daily", budget_status(workspace))

    def test_skill_safety_rows_and_upstream_immutability(self) -> None:
        workspace = self.make_workspace()
        rows = {row["name"]: row for row in skill_safety_rows(workspace)}
        self.assertIn("hermes-test-driven-development", rows)
        self.assertEqual(rows["hermes-test-driven-development"]["immutable"], "yes")
        self.assertTrue(rows["hermes-test-driven-development"]["hash"])
        records = {skill.name: skill for skill in discover_skills(workspace)}
        self.assertTrue(immutable_skill(workspace, records["hermes-test-driven-development"].path))
        config = {row["check"]: row for row in skill_config_rows(workspace)}
        self.assertIn("registry-consistency", config)
        self.assertIn("skill-safety", config)

    def test_validate_agents_reports_missing_allowlist_skills(self) -> None:
        workspace = self.make_workspace()
        workspace.config["agents"]["list"].append(
            {"id": "bad-agent", "role": "Broken", "skills": ["missing-skill"], "runner": "dry-run"}
        )
        errors, warnings = validate_agents(workspace)
        self.assertEqual(warnings, [])
        self.assertIn("bad-agent: configured skill not found: missing-skill", errors)

    def test_create_skill_and_self_improvement_apply(self) -> None:
        workspace = self.make_workspace()
        create_skill(workspace, "release checklist", "Review release readiness.", "custom")
        append_lesson(
            workspace,
            "LESSON: release-checklist should verify docs and tests before shipping.",
            "release-checklist",
        )
        proposal = propose_improvement(workspace, skill_name="release-checklist")
        target = apply_improvement(workspace, proposal.name, "release-checklist", yes=True)
        text = target.read_text(encoding="utf-8")
        self.assertIn("Learned Procedure", text)
        self.assertIn("release-checklist should verify docs", text)

    def test_web_status_and_run_api(self) -> None:
        workspace = self.make_workspace()

        class BoundHandler(Handler):
            pass

        BoundHandler.workspace = workspace
        server = ThreadingHTTPServer(("127.0.0.1", 0), BoundHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        host, port = server.server_address

        with urlopen(f"http://{host}:{port}/api/status", timeout=5) as response:
            status = json.loads(response.read().decode("utf-8"))
        self.assertGreaterEqual(len(status["skills"]), 1)
        self.assertGreaterEqual(len(status["agents"]), 1)
        self.assertIn("metrics", status)
        self.assertIn("jobs", status)
        self.assertIn("models", status)
        self.assertIn("auth", status)
        self.assertIn("api", status)
        self.assertIn("gateway", status)
        self.assertIn("setup", status)
        self.assertIn("skillConfig", status)
        self.assertIn("approvals", status)
        self.assertIn("learningProposals", status)
        self.assertIn("reliability", status)
        self.assertIn("traces", status)
        self.assertIn("health", status)
        self.assertIn("budget", status)
        self.assertIn("morpheus", status)
        self.assertIn("daemon", status)
        self.assertIn("schedules", status)

        proposed = propose_action(
            workspace,
            category="file",
            title="Dashboard approval file",
            description="Approval API smoke.",
            payload={"path": "approved/dashboard.txt", "content": "ok"},
            origin="unit-test",
        )
        approval_body = json.dumps({"id": proposed["id"], "action": "approve"}).encode("utf-8")
        approval_request = Request(
            f"http://{host}:{port}/api/approvals",
            data=approval_body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(approval_request, timeout=5) as response:
            approval_payload = json.loads(response.read().decode("utf-8"))
        self.assertIn("approval", approval_payload)
        self.assertTrue((workspace.root / "approved" / "dashboard.txt").exists())

        morpheus_body = json.dumps({"dryRun": True}).encode("utf-8")
        morpheus_request = Request(
            f"http://{host}:{port}/api/morpheus",
            data=morpheus_body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(morpheus_request, timeout=5) as response:
            morpheus_payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(morpheus_payload["morpheus"]["status"], "dry-run")

        body = json.dumps({"agent": "planner", "model": "packet", "task": "Plan a release"}).encode("utf-8")
        request = Request(
            f"http://{host}:{port}/api/run",
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            run = json.loads(response.read().decode("utf-8"))
        self.assertIn("record", run)
        self.assertIn("dashboard", run)
        self.assertTrue(Path(run["record"]).exists())

        chat_body = json.dumps({"agent": "chat", "model": "packet", "message": "Hello"}).encode("utf-8")
        chat_request = Request(
            f"http://{host}:{port}/api/chat",
            data=chat_body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(chat_request, timeout=5) as response:
            chat = json.loads(response.read().decode("utf-8"))
        self.assertEqual(chat["status"], "packet-only")
        self.assertIn("reply", chat)

    def test_gateway_status_and_run_api(self) -> None:
        workspace = self.make_workspace()
        workspace.config["gateway"]["tokenEnv"] = "BIRKIN_TEST_GATEWAY_TOKEN"
        workspace.save_config()

        class BoundGateway(GatewayHandler):
            pass

        BoundGateway.workspace = workspace
        server = ThreadingHTTPServer(("127.0.0.1", 0), BoundGateway)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        host, port = server.server_address

        with urlopen(f"http://{host}:{port}/health", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
        self.assertEqual(health["status"], "ok")

        with urlopen(f"http://{host}:{port}/api/models", timeout=5) as response:
            models = json.loads(response.read().decode("utf-8"))
        self.assertGreaterEqual(len(models["models"]), 1)

        with urlopen(f"http://{host}:{port}/api/setup", timeout=5) as response:
            setup = json.loads(response.read().decode("utf-8"))
        self.assertIn("checks", setup)

        with urlopen(f"http://{host}:{port}/api/ledger", timeout=5) as response:
            ledger = json.loads(response.read().decode("utf-8"))
        self.assertIn("ledger", ledger)

        with urlopen(f"http://{host}:{port}/api/learning", timeout=5) as response:
            learning = json.loads(response.read().decode("utf-8"))
        self.assertIn("proposals", learning)

        with urlopen(f"http://{host}:{port}/api/reliability", timeout=5) as response:
            reliability = json.loads(response.read().decode("utf-8"))
        self.assertIn("health", reliability)
        self.assertIn("budget", reliability)

        with urlopen(f"http://{host}:{port}/api/memory", timeout=5) as response:
            memory = json.loads(response.read().decode("utf-8"))
        self.assertIn("memory", memory)

        proposed = propose_action(
            workspace,
            category="file",
            title="Gateway approval file",
            description="Gateway approval API smoke.",
            payload={"path": "approved/gateway.txt", "content": "ok"},
            origin="unit-test",
        )
        with urlopen(f"http://{host}:{port}/api/approvals", timeout=5) as response:
            approvals_payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(len(approvals_payload["approvals"]), 1)
        approval_body = json.dumps({"id": proposed["id"], "action": "approve"}).encode("utf-8")
        approval_request = Request(
            f"http://{host}:{port}/api/approvals",
            data=approval_body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(approval_request, timeout=5) as response:
            approval_result = json.loads(response.read().decode("utf-8"))
        self.assertIn("approval", approval_result)
        self.assertTrue((workspace.root / "approved" / "gateway.txt").exists())

        morpheus_body = json.dumps({"dryRun": True}).encode("utf-8")
        morpheus_request = Request(
            f"http://{host}:{port}/api/morpheus",
            data=morpheus_body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(morpheus_request, timeout=5) as response:
            morpheus_payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(morpheus_payload["morpheus"]["status"], "dry-run")

        body = json.dumps({"agent": "planner", "model": "packet", "task": "Plan a release"}).encode("utf-8")
        request = Request(
            f"http://{host}:{port}/api/run",
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            run = json.loads(response.read().decode("utf-8"))
        self.assertIn("record", run)
        self.assertFalse(run["result"]["executed"])

        chat_body = json.dumps({"agent": "chat", "model": "packet", "message": "Hello"}).encode("utf-8")
        chat_request = Request(
            f"http://{host}:{port}/api/chat",
            data=chat_body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(chat_request, timeout=5) as response:
            chat = json.loads(response.read().decode("utf-8"))
        self.assertEqual(chat["chat"]["status"], "packet-only")


if __name__ == "__main__":
    unittest.main()
