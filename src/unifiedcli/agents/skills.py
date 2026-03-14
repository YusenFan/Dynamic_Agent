"""SkillManager — discover, load, and install skills for agents.

Three basic skills are available to ALL agents (main agent and subagents):
  - find-skills:    Discover and install skills from the ecosystem
  - browser-use:    Browse the web for research and information gathering
  - skill-creator:  Create new skills when no existing skill fits

On agent creation, the SkillManager:
  1. Loads all basic skills
  2. Matches additional skills based on the task description and spawn reason
  3. If no match is found, the agent can use browser-use + skill-creator at runtime
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


BASIC_SKILL_NAMES = ["find-skills", "browser-use", "skill-creator"]


@dataclass
class SkillInfo:
    """Parsed skill metadata from SKILL.md frontmatter."""
    name: str
    description: str
    path: Path
    is_basic: bool = False


class SkillManager:
    """Manages skill discovery, matching, and installation for agents."""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self._catalog: dict[str, SkillInfo] = {}
        self._scan()

    def _scan(self) -> None:
        """Scan the skills directory and build the catalog."""
        if not self.skills_dir.exists():
            return
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            info = _parse_skill_md(skill_md)
            if info:
                info.is_basic = info.name in BASIC_SKILL_NAMES
                self._catalog[info.name] = info

    def get_basic_skills(self) -> list[SkillInfo]:
        """Return the 3 basic skills available to all agents."""
        return [
            self._catalog[name]
            for name in BASIC_SKILL_NAMES
            if name in self._catalog
        ]

    def get_skill(self, name: str) -> SkillInfo | None:
        return self._catalog.get(name)

    def list_all(self) -> list[SkillInfo]:
        return list(self._catalog.values())

    def match_skills(
        self,
        task_description: str,
        spawn_reason: str,
        capability_tags: list[str] | None = None,
    ) -> list[SkillInfo]:
        """Find skills relevant to a task based on description, reason, and tags.

        Matches by checking if any words from the task context appear in the
        skill description. Basic skills are excluded (they're always loaded).
        """
        context = f"{task_description} {spawn_reason} {' '.join(capability_tags or [])}".lower()
        context_words = set(context.split())

        matched: list[SkillInfo] = []
        for info in self._catalog.values():
            if info.is_basic:
                continue
            desc_words = set(info.description.lower().split())
            # Match if there's meaningful overlap (at least 2 shared words,
            # excluding very common words)
            shared = context_words & desc_words - _STOP_WORDS
            if len(shared) >= 2:
                matched.append(info)

        return matched

    def install_for_agent(
        self,
        task_description: str,
        spawn_reason: str,
        capability_tags: list[str] | None = None,
    ) -> list[str]:
        """Determine which skills to install for a new agent.

        Returns list of skill names: basic skills + matched skills.
        """
        installed = [s.name for s in self.get_basic_skills()]

        matched = self.match_skills(task_description, spawn_reason, capability_tags)
        for skill in matched:
            if skill.name not in installed:
                installed.append(skill.name)

        return installed


def _parse_skill_md(path: Path) -> SkillInfo | None:
    """Parse SKILL.md frontmatter to extract name and description."""
    text = path.read_text()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict) or "name" not in meta:
        return None
    return SkillInfo(
        name=meta["name"],
        description=meta.get("description", ""),
        path=path.parent,
    )


# Common words to ignore when matching skills to tasks
_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "don", "now", "and", "but", "or", "if", "this", "that", "it", "its",
    "use", "used", "using",
}
