"""SkillScanner 单元测试"""

import tempfile
import pytest
from pathlib import Path
from tenant.services.marketplace.skill_scanner import SkillMeta, SkillScanner


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


def test_parse_skill_file_valid():
    """验证解析有效的 SKILL.md 文件"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Use when testing skill parsing
version: 2.0.0
author: test-author
tags: [test, parsing]
---

# Test Skill

This is a test skill.
""", encoding="utf-8")

        skill = scanner.parse_skill_file(skill_file)

        assert skill.name == "test-skill"
        assert skill.description == "Use when testing skill parsing"
        assert skill.version == "2.0.0"
        assert skill.author == "test-author"
        assert skill.tags == ["test", "parsing"]
        assert skill.skill_dir == Path(tmpdir)


def test_parse_skill_file_missing_name():
    """验证缺少必需字段 name 时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
description: Missing name field
---

# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="missing 'name' field"):
            scanner.parse_skill_file(skill_file)


def test_parse_skill_file_missing_description():
    """验证缺少必需字段 description 时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
---

# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="missing 'description' field"):
            scanner.parse_skill_file(skill_file)


def test_parse_skill_file_invalid_yaml():
    """验证 YAML 格式错误时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: [invalid yaml
---

# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="YAML parse error"):
            scanner.parse_skill_file(skill_file)
