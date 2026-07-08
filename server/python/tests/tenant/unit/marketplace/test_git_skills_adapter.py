"""Git 仓库 Skill 适配器测试"""

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tenant.services.marketplace.adapters.git_skills_adapter import GitSkillsAdapter
from tenant.services.marketplace.skill_scanner import SkillMeta


def _make_skill_meta(
    name: str = "test-skill",
    description: str = "A test skill",
    version: str = "1.0.0",
    author: str = "testauthor",
    tags: list[str] | None = None,
    skill_dir: Path | None = None,
) -> SkillMeta:
    """创建测试用 SkillMeta"""
    return SkillMeta(
        name=name,
        description=description,
        version=version,
        author=author,
        tags=tags or [],
        skill_dir=skill_dir,
    )


class TestGitSkillsAdapterInit:
    """GitSkillsAdapter 初始化和 market_type 测试"""

    def test_market_type(self):
        """验证 market_type 为 git-skills"""
        adapter = GitSkillsAdapter()
        assert adapter.market_type == "git-skills"

    def test_default_repo(self):
        """验证默认仓库 URL"""
        assert GitSkillsAdapter.DEFAULT_REPO == "https://github.com/anthropics/skills.git"

    def test_default_ref(self):
        """验证默认分支"""
        assert GitSkillsAdapter.DEFAULT_REF == "main"

    def test_custom_dependencies(self):
        """验证可注入自定义依赖"""
        mock_sync = MagicMock()
        mock_scanner = MagicMock()
        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        assert adapter.git_sync is mock_sync
        assert adapter.scanner is mock_scanner


class TestGitSkillsAdapterListPlugins:
    """GitSkillsAdapter.list_plugins 测试"""

    @pytest.mark.asyncio
    async def test_list_plugins_basic(self, tmp_path: Path):
        """验证基本 list_plugins 功能"""
        # 创建测试 Skill 目录
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
version: 1.0.0
author: testauthor
tags:
  - python
---
Content
""")

        # Mock git_sync
        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        # Mock scanner
        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = [
            _make_skill_meta(tags=["python"], skill_dir=skill_dir),
        ]

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {
            "repo_url": "https://github.com/test/repo.git",
            "ref": "main",
        }

        plugins, total = await adapter.list_plugins(config)

        assert total == 1
        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.plugin_id == "testauthor/test-skill"
        assert plugin.name == "test-skill"
        assert plugin.description == "A test skill"
        assert plugin.version == "main"  # ref 作为版本
        assert plugin.author == "testauthor"
        assert plugin.plugin_type == "skill"
        assert plugin.tags == ["python"]
        assert plugin.download_url == "git://https://github.com/test/repo.git:main:test-skill"

    @pytest.mark.asyncio
    async def test_list_plugins_keyword_filter(self, tmp_path: Path):
        """验证关键词过滤"""
        skill1_dir = tmp_path / "python-skill"
        skill1_dir.mkdir()
        skill2_dir = tmp_path / "rust-skill"
        skill2_dir.mkdir()

        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = [
            _make_skill_meta(name="python-skill", description="A Python skill", skill_dir=skill1_dir),
            _make_skill_meta(name="rust-skill", description="A Rust skill", skill_dir=skill2_dir),
        ]

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        plugins, total = await adapter.list_plugins(config, keyword="python")

        assert total == 1
        assert len(plugins) == 1
        assert plugins[0].name == "python-skill"

    @pytest.mark.asyncio
    async def test_list_plugins_pagination(self, tmp_path: Path):
        """验证分页功能"""
        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        skills = [
            _make_skill_meta(name=f"skill-{i}", description=f"Skill {i}", author="author")
            for i in range(5)
        ]
        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = skills

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        # 第1页，每页2条
        plugins, total = await adapter.list_plugins(config, page=1, page_size=2)
        assert total == 5
        assert len(plugins) == 2

        # 第2页
        plugins, total = await adapter.list_plugins(config, page=2, page_size=2)
        assert total == 5
        assert len(plugins) == 2

        # 第3页（只有1条）
        plugins, total = await adapter.list_plugins(config, page=3, page_size=2)
        assert total == 5
        assert len(plugins) == 1

    @pytest.mark.asyncio
    async def test_list_plugins_default_config(self, tmp_path: Path):
        """验证使用默认 repo_url 和 ref"""
        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = []

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {}  # 空 config，使用默认值

        plugins, total = await adapter.list_plugins(config)

        mock_sync.sync_repo.assert_called_once_with(
            GitSkillsAdapter.DEFAULT_REPO,
            GitSkillsAdapter.DEFAULT_REF,
        )
        assert total == 0


class TestGitSkillsAdapterGetPlugin:
    """GitSkillsAdapter.get_plugin 测试"""

    @pytest.mark.asyncio
    async def test_get_plugin_found(self, tmp_path: Path):
        """验证找到插件"""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = [
            _make_skill_meta(name="my-skill", author="myauthor", skill_dir=skill_dir),
        ]

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        plugin = await adapter.get_plugin(config, "myauthor/my-skill")

        assert plugin is not None
        assert plugin.plugin_id == "myauthor/my-skill"
        assert plugin.name == "my-skill"

    @pytest.mark.asyncio
    async def test_get_plugin_not_found(self, tmp_path: Path):
        """验证未找到插件返回 None"""
        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = []

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        plugin = await adapter.get_plugin(config, "nonexistent/plugin")

        assert plugin is None


class TestGitSkillsAdapterDownloadPlugin:
    """GitSkillsAdapter.download_plugin 测试"""

    @pytest.mark.asyncio
    async def test_download_plugin_returns_valid_zip(self, tmp_path: Path):
        """验证下载插件返回有效 ZIP（含 SKILL.md）"""
        skill_dir = tmp_path / "download-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: download-skill
description: Downloadable skill
version: 1.0.0
author: dlauthor
---
Content
""")
        (skill_dir / "helper.py").write_text("def help(): pass")

        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        skill_meta = _make_skill_meta(
            name="download-skill",
            author="dlauthor",
            skill_dir=skill_dir,
        )
        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = [skill_meta]

        # 使用真实 zip_skill
        from tenant.services.marketplace.skill_scanner import SkillScanner
        real_scanner = SkillScanner()
        zip_data, expected_checksum = real_scanner.zip_skill(skill_meta)
        mock_scanner.zip_skill.return_value = (zip_data, expected_checksum)

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        data, checksum = await adapter.download_plugin(config, "dlauthor/download-skill")

        # 验证是有效 ZIP
        assert zipfile.is_zipfile(BytesIO(data))
        with zipfile.ZipFile(BytesIO(data)) as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert "helper.py" in names

        # 验证校验和
        assert checksum == hashlib.sha256(data).hexdigest()

    @pytest.mark.asyncio
    async def test_download_plugin_not_found(self, tmp_path: Path):
        """验证下载不存在的插件抛出 ValueError"""
        mock_sync = AsyncMock()
        mock_sync.sync_repo.return_value = (tmp_path, "abc123")

        mock_scanner = MagicMock()
        mock_scanner.scan_skills.return_value = []

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        with pytest.raises(ValueError, match="Skill not found: nonexistent/plugin"):
            await adapter.download_plugin(config, "nonexistent/plugin")


class TestGitSkillsAdapterTestConnection:
    """GitSkillsAdapter.test_connection 测试"""

    @pytest.mark.asyncio
    async def test_connection_success(self):
        """验证连接成功"""
        mock_sync = AsyncMock()
        mock_sync.check_repo_accessible.return_value = True

        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        result = await adapter.test_connection(config)

        assert result.success is True
        assert "成功" in result.message
        mock_sync.check_repo_accessible.assert_called_once_with(
            "https://github.com/test/repo.git", "main"
        )

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """验证连接失败"""
        mock_sync = AsyncMock()
        mock_sync.check_repo_accessible.return_value = False

        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        result = await adapter.test_connection(config)

        assert result.success is False
        assert "失败" in result.message

    @pytest.mark.asyncio
    async def test_connection_default_config(self):
        """验证使用默认配置测试连接"""
        mock_sync = AsyncMock()
        mock_sync.check_repo_accessible.return_value = True

        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {}

        result = await adapter.test_connection(config)

        assert result.success is True
        mock_sync.check_repo_accessible.assert_called_once_with(
            GitSkillsAdapter.DEFAULT_REPO,
            GitSkillsAdapter.DEFAULT_REF,
        )


class TestGitSkillsAdapterCheckUpdates:
    """GitSkillsAdapter.check_updates 测试"""

    @pytest.mark.asyncio
    async def test_check_updates_has_update(self):
        """验证检测到更新"""
        mock_sync = AsyncMock()
        mock_sync.get_remote_commit_sha.return_value = "new_sha_abc"

        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        plugins = [
            {"plugin_id": "author/skill1", "current_version": "old_sha_xyz"},
        ]

        results = await adapter.check_updates(config, plugins)

        assert len(results) == 1
        assert results[0].plugin_id == "author/skill1"
        assert results[0].current_version == "old_sha_xyz"
        assert results[0].latest_version == "new_sha_abc"
        assert results[0].has_update is True

    @pytest.mark.asyncio
    async def test_check_updates_no_update(self):
        """验证无更新"""
        mock_sync = AsyncMock()
        mock_sync.get_remote_commit_sha.return_value = "same_sha"

        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        plugins = [
            {"plugin_id": "author/skill1", "current_version": "same_sha"},
        ]

        results = await adapter.check_updates(config, plugins)

        assert len(results) == 1
        assert results[0].has_update is False

    @pytest.mark.asyncio
    async def test_check_updates_empty_plugins(self):
        """验证空插件列表"""
        mock_sync = AsyncMock()
        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        results = await adapter.check_updates(config, [])

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_check_updates_remote_sha_empty(self):
        """验证远程 SHA 为空时（仓库不可访问）"""
        mock_sync = AsyncMock()
        mock_sync.get_remote_commit_sha.return_value = ""

        mock_scanner = MagicMock()

        adapter = GitSkillsAdapter(git_sync=mock_sync, scanner=mock_scanner)
        config = {"repo_url": "https://github.com/test/repo.git", "ref": "main"}

        plugins = [
            {"plugin_id": "author/skill1", "current_version": "old_sha"},
        ]

        results = await adapter.check_updates(config, plugins)

        # 远程 SHA 为空，无法比较，不应报告更新
        assert len(results) == 1
        assert results[0].has_update is True  # "" != "old_sha"
