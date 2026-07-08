"""Skill 扫描工具"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SkillMeta:
    """Skill 元数据

    符合 agentskills.io/specification 规范。
    """

    name: str                    # 必需：skill 名称
    description: str             # 必需：描述
    version: str = "1.0.0"       # 版本
    author: str = "unknown"      # 作者
    tags: list[str] = field(default_factory=list)
    skill_dir: Path | None = None  # 扫描时填充：skill 目录路径


class SkillScanner:
    """Skill 扫描工具"""

    def parse_skill_file(self, skill_file: Path) -> SkillMeta:
        """解析单个 SKILL.md 文件"""
        if not skill_file.exists():
            raise ValueError(f"Skill file not found: {skill_file}")

        content = skill_file.read_text(encoding="utf-8")

        if not content.startswith("---"):
            raise ValueError("Invalid SKILL.md format: missing front matter delimiter")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid SKILL.md format: malformed front matter")

        front_matter_text = parts[1].strip()

        try:
            front_matter = yaml.safe_load(front_matter_text)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parse error: {e}") from e

        if not isinstance(front_matter, dict):
            raise ValueError("Invalid SKILL.md format: front matter must be a YAML map")

        name = front_matter.get("name")
        if not name:
            raise ValueError("Invalid SKILL.md format: missing 'name' field")

        description = front_matter.get("description")
        if not description:
            raise ValueError("Invalid SKILL.md format: missing 'description' field")

        version = front_matter.get("version", "1.0.0")
        author = front_matter.get("author", "unknown")
        tags = front_matter.get("tags", [])

        return SkillMeta(
            name=name,
            description=description,
            version=version,
            author=author,
            tags=tags if isinstance(tags, list) else [],
            skill_dir=skill_file.parent,
        )
