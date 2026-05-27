from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

from birkin_agent.agents import build_packet, run_agent, validate_agents
from birkin_agent.dashboard import dashboard_data
from birkin_agent.improve import append_lesson, apply_improvement, propose_improvement
from birkin_agent.models import render_model_command, resolve_model_profile, use_model_profile, validate_models
from birkin_agent.skills import create_skill, discover_skills, validate_skills
from birkin_agent.web import Handler
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
        self.assertTrue((workspace.root / "scripts" / "birkin").exists())
        self.assertTrue((workspace.root / "scripts" / "birkin.ps1").exists())

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
        self.assertGreaterEqual(data["metrics"]["modelsTotal"], 3)

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


if __name__ == "__main__":
    unittest.main()
