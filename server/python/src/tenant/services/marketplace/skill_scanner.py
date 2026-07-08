"""Skill 扫描工具"""

from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import yaml
from loguru import logger


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

    def scan_skills(self, base_dir: Path) -> list[SkillMeta]:
        """递归扫描目录中的所有 SKILL.md"""
        skills = []
        for skill_file in base_dir.rglob("SKILL.md"):
            try:
                skill = self.parse_skill_file(skill_file)
                skills.append(skill)
            except ValueError as e:
                logger.warning(f"Failed to parse {skill_file}: {e}")
        return skills

    def zip_skill(self, skill: SkillMeta) -> tuple[bytes, str]:
        """将 skill 目录打包为 ZIP"""
        if not skill.skill_dir:
            raise ValueError("skill_dir is not set")

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill.skill_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill.skill_dir)
                    zipf.write(file_path, arcname)

        zip_data = zip_buffer.getvalue()
        checksum = hashlib.sha256(zip_data).hexdigest()
        return zip_data, checksum
