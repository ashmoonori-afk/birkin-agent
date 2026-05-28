from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / ".refs"
HERMES = REFS / "hermes-agent"
OPENCLAW = REFS / "openclaw"
UPSTREAM_ROOT = ROOT / "skills" / "upstream"


def git_head(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def ensure_inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise RuntimeError(f"refusing to touch path outside {root_resolved}: {resolved}") from exc
    return resolved


def first_frontmatter_value(text: str, key: str) -> str:
    if not text.startswith("---\n"):
        return ""
    lines = text.splitlines()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return ""


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def mirror_tree(source: Path, target: Path) -> None:
    target = ensure_inside(target, ROOT)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def write_reflection(
    target: Path,
    prefix: str,
    upstream_name: str,
    upstream_rel: Path,
    upstream_text: str,
    commit: str,
    source_key: str,
    category: str,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    description = clean_scalar(first_frontmatter_value(upstream_text, "description"))
    platforms = first_frontmatter_value(upstream_text, "platforms") or "[windows, linux, macos]"
    mirror_rel = Path("skills") / "upstream" / source_key / upstream_rel
    source_metadata = {
        "category": category,
        "tags": [source_key, "bundled-skill", "upstream-skill"],
        "upstreamCommit": commit,
        "upstreamPath": (Path("skills") / upstream_rel).as_posix(),
        "upstreamSkill": upstream_name,
    }
    metadata = {
        "birkin": {
            "alwaysInclude": True,
            "capabilityLevel": "upstream-skill",
            "upstreamMirror": mirror_rel.as_posix(),
        },
        source_key: source_metadata,
    }
    if source_key != "hermes":
        metadata["hermes"] = {
            "tags": [source_key, "bundled-skill", "upstream-skill"],
            "category": category,
        }
    content = "\n".join(
        [
            "---",
            f"name: {prefix}-{upstream_name}",
            f"description: {json.dumps(description, ensure_ascii=False)}",
            "version: 0.2.0",
            f"platforms: {platforms}",
            f"metadata: {json.dumps(metadata, ensure_ascii=False, separators=(',', ':'))}",
            "---",
            "",
            f"# {prefix.title()} Upstream Skill: {upstream_name}",
            "",
            "## Birkin Integration",
            "",
            f"The exact upstream skill directory is mirrored at `{mirror_rel.as_posix()}`.",
            "",
            "When a run asks to include skill bodies, Birkin loads the mirrored upstream `SKILL.md` from that directory.",
            "",
            "## Verification",
            "",
            f"- Upstream source: `{(Path('skills') / upstream_rel).as_posix()}`",
            f"- Upstream commit: `{commit}`",
            "- The mirrored directory contains the exact upstream files fetched by `tools/sync_upstream_skills.py`.",
            "",
        ]
    )
    target.write_text(content, encoding="utf-8")


def sync_hermes() -> list[dict[str, str]]:
    commit = git_head(HERMES)
    rows: list[dict[str, str]] = []
    for skill_file in sorted((HERMES / "skills").rglob("SKILL.md")):
        skill_dir = skill_file.parent
        rel = skill_dir.relative_to(HERMES / "skills")
        category = rel.parts[0] if rel.parts else skill_dir.parent.name
        upstream_name = skill_dir.name
        mirror_tree(skill_dir, UPSTREAM_ROOT / "hermes" / rel)
        write_reflection(
            ROOT / "skills" / "hermes-reflections" / upstream_name / "SKILL.md",
            "hermes",
            upstream_name,
            rel,
            skill_file.read_text(encoding="utf-8"),
            commit,
            "hermes",
            category,
        )
        rows.append(
            {
                "source": "hermes",
                "name": upstream_name,
                "category": category,
                "path": (Path("skills") / rel).as_posix(),
                "commit": commit,
            }
        )
    return rows


def sync_openclaw() -> list[dict[str, str]]:
    commit = git_head(OPENCLAW)
    rows: list[dict[str, str]] = []
    for skill_file in sorted((OPENCLAW / "skills").glob("*/SKILL.md")):
        skill_dir = skill_file.parent
        upstream_name = skill_dir.name
        rel = skill_dir.relative_to(OPENCLAW / "skills")
        mirror_tree(skill_dir, UPSTREAM_ROOT / "openclaw" / rel)
        write_reflection(
            ROOT / "skills" / "openclaw-reflections" / upstream_name / "SKILL.md",
            "openclaw",
            upstream_name,
            rel,
            skill_file.read_text(encoding="utf-8"),
            commit,
            "openclaw",
            "openclaw",
        )
        rows.append(
            {
                "source": "openclaw",
                "name": upstream_name,
                "category": "openclaw",
                "path": (Path("skills") / rel).as_posix(),
                "commit": commit,
            }
        )
    return rows


def main() -> int:
    if not (HERMES / ".git").exists():
        raise SystemExit("missing .refs/hermes-agent; clone NousResearch/hermes-agent first")
    if not (OPENCLAW / ".git").exists():
        raise SystemExit("missing .refs/openclaw; clone openclaw/openclaw first")
    for rel in [
        Path("skills") / "hermes-reflections",
        Path("skills") / "openclaw-reflections",
        Path("skills") / "upstream" / "hermes",
        Path("skills") / "upstream" / "openclaw",
    ]:
        target = ensure_inside(ROOT / rel, ROOT)
        if target.exists():
            shutil.rmtree(target)
    rows = sync_hermes() + sync_openclaw()
    manifest = {
        "generatedBy": "tools/sync_upstream_skills.py",
        "hermesCommit": git_head(HERMES),
        "openclawCommit": git_head(OPENCLAW),
        "total": len(rows),
        "skills": rows,
    }
    (UPSTREAM_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"synced {len(rows)} upstream skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
