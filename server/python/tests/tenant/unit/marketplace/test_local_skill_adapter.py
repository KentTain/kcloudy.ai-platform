"""本地文件 Skill 扫描适配器测试"""

import tempfile
from pathlib import Path

import pytest

from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter


class TestLocalSkillAdapter:
    """LocalSkillAdapter 测试"""

    def test_market_type(self):
        """验证市场类型为 local-skill"""
        adapter = LocalSkillAdapter()
        assert adapter.market_type == "local-skill"

    def test_parse_skill_file_with_front_matter(self, tmp_path: Path):
        """验证 YAML front matter 解析"""
        # 创建测试 SKILL.md 文件
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
version: 1.0.0
author: testuser
metadata:
  hermes:
    tags:
      - python
      - testing
---

# Test Skill Content

This is the skill content.
""")

        adapter = LocalSkillAdapter()
        result = adapter._parse_skill_file(skill_file)

        assert result["name"] == "test-skill"
        assert result["description"] == "A test skill"
        assert result["version"] == "1.0.0"
        assert result["author"] == "testuser"
        assert result["tags"] == ["python", "testing"]

    def test_parse_skill_file_without_author(self, tmp_path: Path):
        """验证默认 author 为 local"""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: no-author-skill
description: Skill without author
version: 0.5.0
---

# Content
""")

        adapter = LocalSkillAdapter()
        result = adapter._parse_skill_file(skill_file)

        assert result["author"] == "local"
        assert result["name"] == "no-author-skill"

    def test_parse_skill_file_invalid_format(self, tmp_path: Path):
        """验证无效格式抛出 ValueError"""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""This is not a valid SKILL.md file.
No front matter here.
""")

        adapter = LocalSkillAdapter()
        with pytest.raises(ValueError, match="Invalid SKILL.md format"):
            adapter._parse_skill_file(skill_file)

    def test_scan_skills_finds_all_skill_files(self, tmp_path: Path):
        """验证递归扫描找到所有 SKILL.md 文件"""
        # 创建目录结构
        (tmp_path / "skill1").mkdir()
        (tmp_path / "skill1" / "SKILL.md").write_text("""---
name: skill1
version: 1.0.0
---
Content 1
""")

        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "skill2").mkdir()
        (tmp_path / "subdir" / "skill2" / "SKILL.md").write_text("""---
name: skill2
version: 2.0.0
---
Content 2
""")

        adapter = LocalSkillAdapter()
        skills = adapter._scan_skills(tmp_path)

        assert len(skills) == 2
        skill_names = {s["name"] for s in skills}
        assert skill_names == {"skill1", "skill2"}

    @pytest.mark.asyncio
    async def test_list_plugins_uses_scan(self, tmp_path: Path):
        """验证 list_plugins 调用 scan_skills"""
        # 创建测试 Skill
        (tmp_path / "test-skill").mkdir()
        (tmp_path / "test-skill" / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
version: 1.0.0
author: tester
metadata:
  hermes:
    tags:
      - test
---
Content
""")

        adapter = LocalSkillAdapter()
        config = {"url": f"file://{tmp_path}"}

        plugins, total = await adapter.list_plugins(config)

        assert total == 1
        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.plugin_id == "tester/test-skill"
        assert plugin.name == "test-skill"
        assert plugin.description == "Test skill"
        assert plugin.version == "1.0.0"
        assert plugin.author == "tester"
        assert plugin.tags == ["test"]
        assert plugin.skill_type == "knowledge"
