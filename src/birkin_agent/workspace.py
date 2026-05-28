from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .defaults import (
    DEFAULT_AGENT_FILES,
    DEFAULT_CONFIG,
    DEFAULT_DOC_FILES,
    DEFAULT_SCRIPT_FILES,
    README,
)
from .util import read_json, safe_path, write_json

CONFIG_NAME = "birkin.json"


class Workspace:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.config_path = self.root / CONFIG_NAME
        self.config: dict[str, Any] = read_json(self.config_path, deepcopy(DEFAULT_CONFIG))

    @classmethod
    def discover(cls, start: Path | None = None) -> "Workspace":
        cursor = (start or Path.cwd()).resolve()
        if cursor.is_file():
            cursor = cursor.parent
        for path in [cursor, *cursor.parents]:
            if (path / CONFIG_NAME).exists():
                return cls(path)
        return cls(cursor)

    def rel(self, *parts: str) -> Path:
        return safe_path(self.root, *parts)

    def save_config(self) -> None:
        write_json(self.config_path, self.config)

    def ensure_dirs(self) -> None:
        for name in [
            "skills",
            ".agents/skills",
            "managed-skills",
            "bundled-skills",
            "runs",
            "usage",
            "memory",
            "learning/proposals/pending",
            "learning/proposals/history",
            "reliability",
            "improvements",
            "approvals/pending",
            "approvals/history",
            "schedules",
            "reviews",
            "docs",
        ]:
            self.rel(name).mkdir(parents=True, exist_ok=True)

    def init(self, force: bool = False) -> list[Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        self.ensure_dirs()
        created: list[Path] = []
        if force or not self.config_path.exists():
            self.save_config()
            created.append(self.config_path)
        for name, content in DEFAULT_AGENT_FILES.items():
            path = self.rel(name)
            if force or not path.exists():
                path.write_text(content, encoding="utf-8")
                created.append(path)
        for name, content in DEFAULT_SCRIPT_FILES.items():
            path = self.rel(name)
            if force or not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                if not path.suffix:
                    path.chmod(path.stat().st_mode | 0o755)
                created.append(path)
        readme = self.rel("README.md")
        if force or not readme.exists():
            readme.write_text(README, encoding="utf-8")
            created.append(readme)
        for name, content in DEFAULT_DOC_FILES.items():
            path = self.rel(name)
            if force or not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                created.append(path)
        return created

    def doctor(self) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if not self.config_path.exists():
            errors.append(f"Missing {CONFIG_NAME}. Run `birkin init`.")
        for prompt_file in self.config.get("workspace", {}).get("promptFiles", []):
            if not self.rel(prompt_file).exists():
                warnings.append(f"Prompt file missing: {prompt_file}")
        for skill_root in self.config.get("skills", {}).get("roots", []):
            path = self.rel(skill_root)
            if not path.exists():
                warnings.append(f"Skill root missing: {skill_root}")
        return errors, warnings
