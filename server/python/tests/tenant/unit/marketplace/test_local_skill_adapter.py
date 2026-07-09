"""本地文件 Skill 扫描适配器测试"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter
from tenant.services.marketplace.skill_scanner import SkillScanner


class TestLocalSkillAdapter:
    """LocalSkillAdapter 测试"""

    def test_market_type(self):
        """验证市场类型为 local-skill"""
        adapter = LocalSkillAdapter()
        assert adapter.market_type == "local-skill"

    def test_dependency_injection_defaults(self):
        """验证默认依赖注入创建 SkillScanner"""
        adapter = LocalSkillAdapter()
        assert isinstance(adapter.scanner, SkillScanner)

    def test_dependency_injection_custom(self):
        """验证自定义依赖注入"""
        mock_scanner = MagicMock(spec=SkillScanner)
        adapter = LocalSkillAdapter(scanner=mock_scanner)
        assert adapter.scanner is mock_scanner

    def test_scanner_parse_skill_file(self, tmp_path: Path):
        """验证通过 scanner 解析 YAML front matter"""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
version: 1.0.0
author: testuser
tags:
  - python
  - testing
---

# Test Skill Content

This is the skill content.
""")

        adapter = LocalSkillAdapter()
        result = adapter.scanner.parse_skill_file(skill_file)

        assert result.name == "test-skill"
        assert result.description == "A test skill"
        assert result.version == "1.0.0"
        assert result.author == "testuser"
        assert result.tags == ["python", "testing"]

    def test_scanner_scan_skills_finds_all(self, tmp_path: Path):
        """验证通过 scanner 递归扫描找到所有 SKILL.md 文件"""
        # 创建目录结构
        (tmp_path / "skill1").mkdir()
        (tmp_path / "skill1" / "SKILL.md").write_text("""---
name: skill1
description: Skill 1
version: 1.0.0
---
Content 1
""")

        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "skill2").mkdir()
        (tmp_path / "subdir" / "skill2" / "SKILL.md").write_text("""---
name: skill2
description: Skill 2
version: 2.0.0
---
Content 2
""")

        adapter = LocalSkillAdapter()
        skills = adapter.scanner.scan_skills(tmp_path)

        assert len(skills) == 2
        skill_names = {s.name for s in skills}
        assert skill_names == {"skill1", "skill2"}

    @pytest.mark.asyncio
    async def test_list_plugins_uses_scan(self, tmp_path: Path):
        """验证 list_plugins 通过 scanner 扫描"""
        # 创建测试 Skill
        (tmp_path / "test-skill").mkdir()
        (tmp_path / "test-skill" / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
version: 1.0.0
author: tester
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

    @pytest.mark.asyncio
    async def test_download_plugin_uses_zip_skill(self, tmp_path: Path):
        """验证 download_plugin 通过 scanner.zip_skill 打包"""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: My skill
version: 1.0.0
author: dev
---
Content
""")
        (skill_dir / "helper.py").write_text("print('hello')")

        adapter = LocalSkillAdapter()
        config = {"url": f"file://{tmp_path}"}

        data, checksum = await adapter.download_plugin(config, "dev/my-skill")

        # 验证返回 ZIP 数据
        assert data[:2] == b"PK"  # ZIP magic bytes
        assert len(checksum) == 64  # SHA256 hex

    @pytest.mark.asyncio
    async def test_download_plugin_not_found(self, tmp_path: Path):
        """验证下载不存在的 Skill 抛出 ValueError"""
        adapter = LocalSkillAdapter()
        config = {"url": f"file://{tmp_path}"}

        with pytest.raises(ValueError, match="Plugin not found"):
            await adapter.download_plugin(config, "nonexistent/skill")
