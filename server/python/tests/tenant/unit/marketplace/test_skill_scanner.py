"""SkillScanner 单元测试"""

import hashlib
import tempfile
import zipfile
from io import BytesIO

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


def test_scan_skills_multiple():
    """验证扫描多个 skill 目录"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        skill1_dir = base_dir / "skill1"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text("""---
name: skill-one
description: First skill
author: author1
---
# Skill One
""", encoding="utf-8")

        skill2_dir = base_dir / "skill2"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text("""---
name: skill-two
description: Second skill
author: author2
---
# Skill Two
""", encoding="utf-8")

        (base_dir / "other_dir").mkdir()

        skills = scanner.scan_skills(base_dir)

        assert len(skills) == 2
        skill_names = [s.name for s in skills]
        assert "skill-one" in skill_names
        assert "skill-two" in skill_names


def test_scan_skills_nested():
    """验证递归扫描嵌套目录"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        nested_dir = base_dir / "category" / "subcategory" / "skill"
        nested_dir.mkdir(parents=True)
        (nested_dir / "SKILL.md").write_text("""---
name: nested-skill
description: Nested skill
---
# Nested
""", encoding="utf-8")

        skills = scanner.scan_skills(base_dir)

        assert len(skills) == 1
        assert skills[0].name == "nested-skill"


def test_zip_skill():
    """验证将 skill 目录打包为 ZIP"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Test skill for zipping
---
# Test Skill
""", encoding="utf-8")

        (skill_dir / "helper.py").write_text("# helper code", encoding="utf-8")
        subdir = skill_dir / "docs"
        subdir.mkdir()
        (subdir / "readme.md").write_text("# Docs", encoding="utf-8")

        skill = SkillMeta(
            name="test-skill",
            description="Test skill for zipping",
            skill_dir=skill_dir,
        )

        zip_data, checksum = scanner.zip_skill(skill)

        assert isinstance(zip_data, bytes)
        assert isinstance(checksum, str)
        assert len(checksum) == 64

        expected_checksum = hashlib.sha256(zip_data).hexdigest()
        assert checksum == expected_checksum

        with zipfile.ZipFile(BytesIO(zip_data)) as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert "helper.py" in names
            assert "docs/readme.md" in names


def test_parse_skill_file_invalid_name_chars():
    """验证 name 包含非法字符时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: invalid name!
description: Has invalid name
---
# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="'name' must start with alphanumeric"):
            scanner.parse_skill_file(skill_file)


def test_parse_skill_file_description_too_long():
    """验证 description 超过 500 字符时抛出异常"""
    scanner = SkillScanner()

    long_desc = "x" * 501

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text(f"""---
name: test-skill
description: {long_desc}
---
# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="exceeds 500 characters"):
            scanner.parse_skill_file(skill_file)


def test_parse_skill_file_name_with_hyphens():
    """验证 name 允许连字符"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: my-cool-skill
description: Valid name with hyphens
---
# Test
""", encoding="utf-8")

        skill = scanner.parse_skill_file(skill_file)
        assert skill.name == "my-cool-skill"
