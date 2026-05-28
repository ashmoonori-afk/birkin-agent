from __future__ import annotations

import tomllib

from .workspace import Workspace


def validate_runtime_dependencies(workspace: Workspace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    path = workspace.rel("pyproject.toml")
    if not path.exists():
        return errors, warnings
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"pyproject.toml cannot be parsed: {exc}")
        return errors, warnings
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    dependencies = project.get("dependencies")
    if dependencies is None:
        return errors, warnings
    if not isinstance(dependencies, list):
        errors.append("project.dependencies must be an array")
        return errors, warnings
    if dependencies:
        errors.append("runtime dependencies must stay empty for the lite core: " + ", ".join(str(item) for item in dependencies))
    return errors, warnings


def runtime_dependency_rows(workspace: Workspace) -> list[dict[str, str]]:
    errors, warnings = validate_runtime_dependencies(workspace)
    status = "error" if errors else "warning" if warnings else "ok"
    detail = "runtime dependency list is empty"
    if errors:
        detail = "; ".join(errors[:2])
    elif warnings:
        detail = "; ".join(warnings[:2])
    return [{"check": "runtime-deps", "status": status, "detail": detail}]
