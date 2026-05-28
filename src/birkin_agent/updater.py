from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


DEFAULT_REPO = "https://github.com/ashmoonori-afk/birkin-agent"
DEFAULT_REF = "main"


def update_spec(repo: str | None = None, ref: str | None = None) -> str:
    selected_repo = repo or os.environ.get("BIRKIN_REPO") or DEFAULT_REPO
    selected_ref = ref or os.environ.get("BIRKIN_REF") or DEFAULT_REF
    return f"git+{selected_repo}@{selected_ref}"


def in_virtualenv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def pip_update_command(spec: str) -> list[str]:
    command = [sys.executable, "-m", "pip", "install", "--upgrade"]
    if not in_virtualenv():
        command.append("--user")
    command.append(spec)
    return command


def choose_update_command(method: str, spec: str) -> tuple[str, list[str]]:
    selected = method.strip().lower() or "auto"
    if selected == "auto":
        if shutil.which("uv"):
            selected = "uv"
        elif shutil.which("pipx"):
            selected = "pipx"
        else:
            selected = "pip"
    if selected == "uv":
        return selected, ["uv", "tool", "install", "--force", spec]
    if selected == "pipx":
        return selected, ["pipx", "install", "--force", spec]
    if selected == "pip":
        return selected, pip_update_command(spec)
    raise ValueError("update method must be auto, uv, pipx, or pip")


def update_self(
    *,
    repo: str | None = None,
    ref: str | None = None,
    method: str = "auto",
    dry_run: bool = False,
    cwd: Path | None = None,
) -> dict[str, Any]:
    spec = update_spec(repo, ref)
    selected, command = choose_update_command(method, spec)
    payload: dict[str, Any] = {
        "status": "dry-run" if dry_run else "running",
        "method": selected,
        "spec": spec,
        "command": command,
    }
    if dry_run:
        return payload
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )
    payload.update(
        {
            "status": "ok" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    )
    return payload
