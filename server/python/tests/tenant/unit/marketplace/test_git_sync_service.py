"""GitSyncService 单元测试"""
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch
import tempfile
from tenant.services.marketplace.git_sync_service import GitSyncService


def test_git_sync_service_default_cache_dir():
    """测试默认缓存目录"""
    service = GitSyncService()
    assert service.cache_dir == Path("./cache/skills")


def test_git_sync_service_custom_cache_dir():
    """测试自定义缓存目录"""
    custom_dir = Path("/tmp/custom/cache")
    service = GitSyncService(cache_dir=custom_dir)
    assert service.cache_dir == custom_dir


def test_get_cache_path():
    """测试获取缓存路径"""
    service = GitSyncService(cache_dir=Path("/tmp/cache"))
    path = service.get_cache_path("https://github.com/anthropics/skills.git", "main")
    assert path == Path("/tmp/cache/github_com_anthropics_skills/main")


def test_get_cache_path_github_url():
    """测试 GitHub URL 缓存路径"""
    service = GitSyncService()
    path = service.get_cache_path("https://github.com/owner/repo.git", "v1.0.0")
    assert "github_com_owner_repo" in str(path)
    assert "v1.0.0" in str(path)


def test_parse_source_url_github_tree():
    """测试解析 GitHub tree URL"""
    service = GitSyncService()
    repo_url, ref, subdir = service.parse_source_url(
        "https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator/skills/skill-creator"
    )
    assert repo_url == "https://github.com/anthropics/claude-plugins-official.git"
    assert ref == "main"
    assert subdir == "plugins/skill-creator/skills/skill-creator"


def test_parse_source_url_github_blob():
    """测试解析 GitHub blob URL"""
    service = GitSyncService()
    repo_url, ref, subdir = service.parse_source_url(
        "https://github.com/owner/repo/blob/v1.0/path/to/file.md"
    )
    assert repo_url == "https://github.com/owner/repo.git"
    assert ref == "v1.0"
    assert subdir == "path/to/file.md"


def test_parse_source_url_git_url():
    """测试解析 .git 结尾的 URL"""
    service = GitSyncService()
    repo_url, ref, subdir = service.parse_source_url("https://github.com/owner/repo.git")
    assert repo_url == "https://github.com/owner/repo.git"
    assert ref == "main"
    assert subdir is None


@pytest.mark.asyncio
async def test_sync_repo_new_clone():
    """测试同步新仓库（克隆场景）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = GitSyncService(cache_dir=Path(tmpdir))
        with patch.object(service, "_clone_repo", new_callable=AsyncMock) as mock_clone:
            mock_clone.return_value = (Path(tmpdir) / "test_repo", "abc123")
            repo_path, commit_sha = await service.sync_repo("https://github.com/test/repo.git", ref="main")
            assert commit_sha == "abc123"
            mock_clone.assert_called_once()


@pytest.mark.asyncio
async def test_sync_repo_existing_cache():
    """测试同步已缓存仓库（fetch 场景）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        service = GitSyncService(cache_dir=cache_dir)

        # 创建已存在的缓存目录和 .git 目录
        cached_repo = cache_dir / "github_com_test_repo" / "main"
        cached_repo.mkdir(parents=True)
        (cached_repo / ".git").mkdir()
        (cached_repo / "SKILL.md").write_text("---\nname: test\n---\n", encoding="utf-8")

        with patch.object(service, "_fetch_and_checkout", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "def456"
            repo_path, commit_sha = await service.sync_repo("https://github.com/test/repo.git", ref="main")
            assert commit_sha == "def456"
            mock_fetch.assert_called_once()
