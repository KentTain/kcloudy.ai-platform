"""SkillScanner 单元测试"""

import pytest
from pathlib import Path
from tenant.services.marketplace.skill_scanner import SkillMeta


def test_skill_meta_creation():
    """验证 SkillMeta 数据类创建"""
    skill = SkillMeta(
        name="test-skill",
        description="Use when testing",
        version="1.0.0",
        author="test-author",
        tags=["test"],
    )
    assert skill.name == "test-skill"
    assert skill.description == "Use when testing"
    assert skill.version == "1.0.0"
    assert skill.author == "test-author"
    assert skill.tags == ["test"]
    assert skill.skill_dir is None


def test_skill_meta_defaults():
    """验证 SkillMeta 默认值"""
    skill = SkillMeta(
        name="minimal-skill",
        description="Minimal description",
    )
    assert skill.version == "1.0.0"
    assert skill.author == "unknown"
    assert skill.tags == []
    assert skill.skill_dir is None
