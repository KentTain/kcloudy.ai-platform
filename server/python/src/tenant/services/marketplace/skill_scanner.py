"""Skill 扫描工具"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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
