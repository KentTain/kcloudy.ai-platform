"""Git 仓库 Skill 适配器"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from tenant.services.marketplace.git_sync_service import GitSyncService
from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)
from tenant.services.marketplace.skill_scanner import SkillMeta, SkillScanner

if TYPE_CHECKING:
    from collections.abc import Sequence


class GitSkillsAdapter(MarketplaceAdapter):
    """Git 仓库 Skill 适配器

    从 Git 仓库同步并扫描 SKILL.md 文件，提供插件市场协议接口。
    复用 GitSyncService 进行仓库同步，SkillScanner 进行 Skill 扫描。
    """

    DEFAULT_REPO = "https://github.com/anthropics/skills.git"
    DEFAULT_REF = "main"

    def __init__(
        self,
        git_sync: GitSyncService | None = None,
        scanner: SkillScanner | None = None,
    ):
        # 尝试从应用配置读取默认值
        try:
            from framework.configs.settings import get_settings
            settings = get_settings()
            git_cfg = settings.skills.git
            self._default_repo = git_cfg.default_repo
            self._default_ref = git_cfg.default_ref
            cache_dir = Path(git_cfg.cache_dir)
        except Exception:
            self._default_repo = self.DEFAULT_REPO
            self._default_ref = self.DEFAULT_REF
            cache_dir = None

        self.git_sync = git_sync or GitSyncService(cache_dir=cache_dir)
        self.scanner = scanner or SkillScanner()
        self._skills_cache: dict[str, tuple[list[SkillMeta], float]] = {}
        self._cache_ttl: float = 60.0  # 缓存 60 秒

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "git-skills"

    def _get_repo_url(self, config: dict) -> str:
        """从配置获取仓库 URL"""
        return config.get("repo_url", self._default_repo)

    def _get_ref(self, config: dict) -> str:
        """从配置获取 Git 引用"""
        return config.get("ref", self._default_ref)

    async def _get_skills(self, repo_url: str, ref: str) -> list[SkillMeta]:
        """获取 skill 列表（带 TTL 缓存）

        同一 repo_url+ref 在 TTL 内不会重复 sync + scan。
        """
        cache_key = f"{repo_url}:{ref}"
        now = time.time()

        if cache_key in self._skills_cache:
            skills, ts = self._skills_cache[cache_key]
            if now - ts < self._cache_ttl:
                return skills

        local_path, _ = await self.git_sync.sync_repo(repo_url, ref)
        skills = self.scanner.scan_skills(local_path)
        self._skills_cache[cache_key] = (skills, now)
        return skills

    def _to_remote_plugin_info(
        self, skill: "SkillMeta", repo_url: str, ref: str
    ) -> RemotePluginInfo:
        """将 SkillMeta 转换为 RemotePluginInfo

        Args:
            skill: Skill 元数据
            repo_url: 仓库 URL
            ref: Git 引用

        Returns:
            RemotePluginInfo 实例
        """
        plugin_id = f"{skill.author}/{skill.name}"
        download_url = f"git://{repo_url}:{ref}:{skill.name}"

        return RemotePluginInfo(
            plugin_id=plugin_id,
            name=skill.name,
            description=skill.description,
            version=skill.version,
            author=skill.author,
            icon=None,
            plugin_type="skill",
            manifest_url=None,
            download_url=download_url,
            created_at=None,
            updated_at=None,
            skill_type="knowledge",
            tags=skill.tags,
        )

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接

        Args:
            config: 市场配置（repo_url, ref）

        Returns:
            MarketplaceTestResult: 测试结果
        """
        repo_url = self._get_repo_url(config)
        ref = self._get_ref(config)

        try:
            accessible = await self.git_sync.check_repo_accessible(repo_url, ref)
            if accessible:
                return MarketplaceTestResult(
                    success=True,
                    message="连接成功",
                )
            return MarketplaceTestResult(
                success=False,
                message=f"连接失败: 仓库 {repo_url} 分支 {ref} 不可访问",
            )
        except Exception as e:
            logger.error(f"测试 Git Skill 市场连接失败: {e}")
            return MarketplaceTestResult(
                success=False,
                message=f"连接异常: {str(e)}",
            )

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取远程插件列表

        同步仓库 -> 扫描 SKILL.md -> 关键词过滤 -> 转换为 RemotePluginInfo -> 分页

        Args:
            config: 市场配置（repo_url, ref）
            keyword: 搜索关键词（过滤 name 和 description）
            plugin_type: 插件类型筛选（当前忽略，全部为 skill）
            page: 页码
            page_size: 每页条数

        Returns:
            tuple[Sequence[RemotePluginInfo], int]: (插件列表, 总数)
        """
        repo_url = self._get_repo_url(config)
        ref = self._get_ref(config)

        try:
            skills = await self._get_skills(repo_url, ref)

            # 关键词过滤
            if keyword:
                keyword_lower = keyword.lower()
                skills = [
                    s for s in skills
                    if keyword_lower in s.name.lower()
                    or keyword_lower in s.description.lower()
                ]

            # 转换为 RemotePluginInfo
            plugins = [self._to_remote_plugin_info(s, repo_url, ref) for s in skills]

            # 分页
            total = len(plugins)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_plugins = plugins[start:end]

            return paginated_plugins, total
        except Exception as e:
            logger.error(f"获取 Git Skill 列表失败: {e}")
            return [], 0

    async def get_plugin(
        self,
        config: dict,
        plugin_id: str,
    ) -> RemotePluginInfo | None:
        """获取单个插件详情

        Args:
            config: 市场配置
            plugin_id: 插件ID（格式：author/name）

        Returns:
            RemotePluginInfo | None: 插件信息，不存在返回 None
        """
        repo_url = self._get_repo_url(config)
        ref = self._get_ref(config)

        try:
            skills = await self._get_skills(repo_url, ref)

            for skill in skills:
                current_plugin_id = f"{skill.author}/{skill.name}"
                if current_plugin_id == plugin_id:
                    return self._to_remote_plugin_info(skill, repo_url, ref)

            return None
        except Exception as e:
            logger.error(f"获取 Git Skill 详情失败: {plugin_id}, 错误: {e}")
            return None

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载插件包

        将 Skill 目录打包为 ZIP 文件。

        Args:
            config: 市场配置
            plugin_id: 插件ID
            version: 版本号（当前忽略，始终使用最新）

        Returns:
            tuple[bytes, str]: (插件包数据, SHA256校验和)

        Raises:
            ValueError: 插件不存在
        """
        repo_url = self._get_repo_url(config)
        ref = self._get_ref(config)

        skills = await self._get_skills(repo_url, ref)

        for skill in skills:
            current_plugin_id = f"{skill.author}/{skill.name}"
            if current_plugin_id == plugin_id:
                zip_data, checksum = self.scanner.zip_skill(skill)
                return zip_data, checksum

        raise ValueError(f"Skill not found: {plugin_id}")

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新

        通过比对远程 commit SHA 和本地版本（local_sha）判断是否有更新。

        Args:
            config: 市场配置
            plugins: 需要检查的插件列表，每项包含 plugin_id, current_version

        Returns:
            Sequence[PluginUpdateInfo]: 更新信息列表
        """
        repo_url = self._get_repo_url(config)
        ref = self._get_ref(config)

        try:
            remote_sha = await self.git_sync.get_remote_commit_sha(repo_url, ref)
        except Exception as e:
            logger.warning(f"获取远程 commit SHA 失败: {e}")
            remote_sha = ""

        results: list[PluginUpdateInfo] = []
        for plugin in plugins:
            plugin_id = plugin.get("plugin_id")
            current_version = plugin.get("current_version", "")

            if not plugin_id:
                continue

            has_update = remote_sha != current_version
            results.append(PluginUpdateInfo(
                plugin_id=plugin_id,
                current_version=current_version,
                latest_version=remote_sha,
                has_update=has_update,
                changelog=None,
            ))

        return results
