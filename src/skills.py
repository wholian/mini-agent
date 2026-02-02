"""Skill data structures for the mini-agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Skill:
    """Represents one loaded skill."""

    name: str
    description: str
    content: str
    skill_path: Path

    def metadata_line(self) -> str:
        """Return one-line metadata used in system prompt injection."""
        return f"- `{self.name}`: {self.description}"

    def full_prompt(self) -> str:
        """Return full skill text for on-demand loading."""
        return (
            f"# Skill: {self.name}\n\n"
            f"{self.description}\n\n"
            f"Skill file: `{self.skill_path}`\n\n"
            f"{self.content}"
        )
