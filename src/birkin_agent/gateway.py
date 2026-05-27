from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from typing import Any
from urllib.parse import urlparse

from .api import api_rows, validate_api
from .agents import run_agent
from .auth import auth_rows, run_auth_command, validate_auth
from .chat import run_chat
from .models import model_rows
from .skills import skill_config_rows
from .workspace import Workspace


ROUTES = [
    "GET /health",
    "GET /routes",
    "GET /api/status",
    "GET /api/models",
    "GET /api/auth",
    "GET /api/api-profiles",
    "GET /api/gateway",
    "GET /api/setup",
    "GET /api/skills/config",
    "POST /api/run",
    "POST /api/chat",
    "POST /api/auth/{profile}/status",
    "POST /api/auth/{profile}/login",
    "POST /api/auth/{profile}/logout",
]


def gateway_config(workspace: Workspace) -> dict[str, Any]:
    return workspace.config.setdefault(
        "gateway",
        {
            "host": "127.0.0.1",
            "port": 8770,
            "tokenEnv": "BIRKIN_GATEWAY_TOKEN",
            "requireToken": False,
        },
    )


def gateway_auth_state(workspace: Workspace) -> tuple[str, str, bool]:
    config = gateway_config(workspace)
    token_env = str(config.get("tokenEnv") or "BIRKIN_GATEWAY_TOKEN")
    token = os.getenv(token_env, "")
    required = bool(config.get("requireToken") or False)
    return token_env, token, bool(required or token)


def gateway_info(workspace: Workspace, host: str | None = None, port: int | None = None) -> dict[str, Any]:
    config = gateway_config(workspace)
    token_env, token, auth_required = gateway_auth_state(workspace)
    return {
        "root": str(workspace.root),
        "host": host or str(config.get("host") or "127.0.0.1"),
        "port": int(port or config.get("port") or 8770),
        "tokenEnv": token_env,
        "authRequired": auth_required,
        "tokenPresent": bool(token),
        "routes": ROUTES,
    }


def validate_gateway(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = gateway_config(workspace)
    host = str(config.get("host") or "127.0.0.1")
    port = config.get("port") or 8770
    token_env, token, auth_required = gateway_auth_state(workspace)
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        errors.append("gateway.port must be an integer")
        port_int = 0
    if port_int < 1 or port_int > 65535:
        errors.append("gateway.port must be between 1 and 65535")
    if bool(config.get("requireToken") or False) and not token:
        errors.append(f"gateway requires token but environment variable is not set: {token_env}")
    if host not in {"127.0.0.1", "localhost", "::1"} and not auth_required:
        warnings.append("gateway is configured for a non-localhost host without token auth")
    return errors, warnings


class GatewayHandler(BaseHTTPRequestHandler):
    workspace: Workspace
    host_label: str = "127.0.0.1"
    port_label: int = 8770

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def authorized(self) -> bool:
        _token_env, token, auth_required = gateway_auth_state(self.workspace)
        if not auth_required:
            return True
        if not token:
            return False
        bearer = self.headers.get("authorization", "")
        header_token = self.headers.get("x-birkin-token", "")
        return bearer == f"Bearer {token}" or header_token == token

    def require_authorized(self) -> bool:
        if self.authorized():
            return True
        self.send_json({"error": "unauthorized"}, 401)
        return False

    def do_GET(self) -> None:
        if not self.require_authorized():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"status": "ok", "service": "birkin-gateway"})
            return
        if parsed.path == "/routes":
            self.send_json({"routes": ROUTES})
            return
        if parsed.path == "/api/status":
            from .dashboard import dashboard_data

            self.send_json(dashboard_data(self.workspace))
            return
        if parsed.path == "/api/models":
            self.send_json({"models": model_rows(self.workspace)})
            return
        if parsed.path == "/api/auth":
            self.send_json({"auth": auth_rows(self.workspace)})
            return
        if parsed.path == "/api/api-profiles":
            self.send_json({"api": api_rows(self.workspace)})
            return
        if parsed.path == "/api/gateway":
            self.send_json(gateway_info(self.workspace, self.host_label, self.port_label))
            return
        if parsed.path == "/api/setup":
            from .setup import setup_report

            self.send_json(setup_report(self.workspace))
            return
        if parsed.path == "/api/skills/config":
            self.send_json({"skillConfig": skill_config_rows(self.workspace)})
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if not self.require_authorized():
            return
        parsed = urlparse(self.path)
        payload = self.read_json()
        if payload is None:
            self.send_json({"error": "invalid json object"}, 400)
            return
        if parsed.path == "/api/run":
            self.handle_run(payload)
            return
        if parsed.path == "/api/chat":
            self.handle_chat(payload)
            return
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "auth":
            profile_id = parts[2]
            action = parts[3]
            if action not in {"login", "logout", "status"}:
                self.send_json({"error": "auth action must be login, logout, or status"}, 400)
                return
            try:
                result = run_auth_command(self.workspace, profile_id, action, interactive=False)
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
                return
            self.send_json({"result": result})
            return
        self.send_json({"error": "not found"}, 404)

    def handle_run(self, payload: dict[str, Any]) -> None:
        agent_id = str(payload.get("agent") or "").strip()
        task = str(payload.get("task") or "").strip()
        runner = str(payload.get("runner") or "").strip() or None
        model = str(payload.get("model") or "").strip() or None
        provider = str(payload.get("provider") or "").strip() or None
        include_skill_bodies = bool(payload.get("includeSkillBodies") or False)
        execute = bool(payload.get("execute") or False)
        if not agent_id or not task:
            self.send_json({"error": "agent and task are required"}, 400)
            return
        try:
            record, result = run_agent(
                self.workspace,
                agent_id,
                task,
                runner_name=runner,
                model_name=model,
                provider_name=provider,
                include_skill_bodies=include_skill_bodies,
                execute=execute,
            )
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)
            return
        from .dashboard import dashboard_data

        self.send_json(
            {
                "record": str(record),
                "result": result,
                "dashboard": dashboard_data(self.workspace),
            }
        )

    def handle_chat(self, payload: dict[str, Any]) -> None:
        message = str(payload.get("message") or "").strip()
        if not message:
            self.send_json({"error": "message is required"}, 400)
            return
        history = payload.get("history") if isinstance(payload.get("history"), list) else []
        try:
            result = run_chat(
                self.workspace,
                message,
                agent_id=str(payload.get("agent") or "").strip() or None,
                model_name=str(payload.get("model") or "").strip() or None,
                provider_name=str(payload.get("provider") or "").strip() or None,
                execute=bool(payload.get("execute") or False),
                history=history,
            )
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)
            return
        self.send_json({"chat": result})


def serve_gateway(workspace: Workspace, host: str | None = None, port: int | None = None) -> None:
    errors, warnings = validate_gateway(workspace)
    auth_errors, auth_warnings = validate_auth(workspace)
    api_errors, api_warnings = validate_api(workspace)
    errors.extend(auth_errors)
    errors.extend(api_errors)
    warnings.extend(auth_warnings)
    warnings.extend(api_warnings)
    for warning in warnings:
        print(f"warning: {warning}")
    if errors:
        raise ValueError("; ".join(errors))

    config = gateway_config(workspace)
    bind_host = host or str(config.get("host") or "127.0.0.1")
    bind_port = int(port or config.get("port") or 8770)

    class BoundGatewayHandler(GatewayHandler):
        pass

    BoundGatewayHandler.workspace = workspace
    BoundGatewayHandler.host_label = bind_host
    BoundGatewayHandler.port_label = bind_port
    server = ThreadingHTTPServer((bind_host, bind_port), BoundGatewayHandler)
    print(f"Birkin Gateway: http://{bind_host}:{bind_port}")
    server.serve_forever()
