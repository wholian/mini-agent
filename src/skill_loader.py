"""Skill loading utilities."""

from __future__ import annotations

import re
from pathlib import Path

from .skills import Skill


class SkillLoader:
    """Load skills from `skills/**/SKILL.md` files."""

    def __init__(self, skills_dir: str = "skills") -> None:
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: dict[str, Skill] = {}

    def load_skill(self, skill_path: Path) -> Skill | None:
        """Load one SKILL.md file."""
        try:
            raw = skill_path.read_text(encoding="utf-8")
        except Exception:
            return None

        match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, flags=re.DOTALL)
        if not match:
            return None

        frontmatter_text = match.group(1).strip()
        body = match.group(2).strip()
        frontmatter = self._parse_frontmatter(frontmatter_text)

        name = frontmatter.get("name", "").strip()
        description = frontmatter.get("description", "").strip()
        if not name or not description:
            return None

        return Skill(
            name=name,
            description=description,
            content=body,
            skill_path=skill_path,
        )

    def discover_skills(self) -> list[Skill]:
        """Discover and load all skills under `skills_dir`."""
        if not self.skills_dir.exists():
            return []

        skills: list[Skill] = []
        for path in self.skills_dir.rglob("SKILL.md"):
            skill = self.load_skill(path)
            if not skill:
                continue
            skills.append(skill)
            self.loaded_skills[skill.name] = skill
        return skills

    def get_skill(self, name: str) -> Skill | None:
        return self.loaded_skills.get(name)

    def get_skills_metadata_prompt(self) -> str:
        """Return metadata-only prompt text for all loaded skills."""
        if not self.loaded_skills:
            return ""
        lines = [
            "## Available Skills",
            "You can load full skill guidance with `get_skill` when needed.",
        ]
        for skill in self.loaded_skills.values():
            lines.append(skill.metadata_line())
        return "\n".join(lines)

    @staticmethod
    def _parse_frontmatter(text: str) -> dict[str, str]:
        """Parse simple `key: value` frontmatter."""
        parsed: dict[str, str] = {}
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            parsed[key.strip()] = value.strip().strip("\"'")
        return parsed
