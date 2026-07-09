"""本地文件 Skill 扫描适配器"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)
from tenant.services.marketplace.skill_scanner import SkillScanner

if TYPE_CHECKING:
    from collections.abc import Sequence


class LocalSkillAdapter(MarketplaceAdapter):
    """本地文件 Skill 扫描适配器

    从本地文件系统扫描 SKILL.md 文件并返回 Skill 信息。
    复用 SkillScanner 进行扫描和打包。
    """

    def __init__(self, scanner: SkillScanner | None = None):
        self.scanner = scanner or SkillScanner()

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "local-skill"

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接

        Args:
            config: 市场配置（必须包含 url 字段）

        Returns:
            MarketplaceTestResult: 测试结果
        """
        url = config.get("url", "")
        if not url:
            return MarketplaceTestResult(success=False, message="市场地址不能为空")

        try:
            # 解析路径
            path = self._parse_url(url)

            if not path.exists():
                return MarketplaceTestResult(success=False, message=f"目录不存在: {path}")

            if not path.is_dir():
                return MarketplaceTestResult(success=False, message=f"路径不是目录: {path}")

            # 扫描 Skill 文件
            skills = self.scanner.scan_skills(path)

            return MarketplaceTestResult(
                success=True,
                message="连接成功",
                plugin_count=len(skills),
            )
        except Exception as e:
            logger.error(f"测试本地 Skill 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取远程插件列表

        Args:
            config: 市场配置
            keyword: 搜索关键词（过滤 name 和 description）
            plugin_type: 插件类型筛选（本地 Skill 忽略此参数）
            page: 页码
            page_size: 每页条数

        Returns:
            tuple[Sequence[RemotePluginInfo], int]: (插件列表, 总数)
        """
        url = config.get("url", "")
        if not url:
            return [], 0

        try:
            path = self._parse_url(url)
            skills = self.scanner.scan_skills(path)

            # 过滤关键词
            if keyword:
                keyword_lower = keyword.lower()
                skills = [
                    s for s in skills
                    if keyword_lower in s.name.lower()
                    or keyword_lower in s.description.lower()
                ]

            # 转换为 RemotePluginInfo
            plugins = []
            for skill in skills:
                skill_dir = skill.skill_dir or path
                plugin_id = f"{skill.author}/{skill.name}"

                plugins.append(RemotePluginInfo(
                    plugin_id=plugin_id,
                    name=skill.name,
                    description=skill.description,
                    version=skill.version,
                    author=skill.author,
                    icon=None,
                    plugin_type="skill",
                    skill_type="knowledge",  # 默认为知识文档
                    tags=skill.tags,
                    downloads=None,
                    manifest_url=None,
                    download_url=f"file://{skill_dir}",
                    created_at=None,
                    updated_at=None,
                ))

            # 分页
            total = len(plugins)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_plugins = plugins[start:end]

            return paginated_plugins, total
        except Exception as e:
            logger.error(f"获取本地 Skill 列表失败: {e}")
            return [], 0

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        """获取单个插件详情

        Args:
            config: 市场配置
            plugin_id: 插件ID（格式：author/name）

        Returns:
            RemotePluginInfo | None: 插件信息，不存在返回 None
        """
        url = config.get("url", "")
        if not url:
            return None

        try:
            path = self._parse_url(url)
            skills = self.scanner.scan_skills(path)

            # 查找匹配的 Skill
            for skill in skills:
                current_plugin_id = f"{skill.author}/{skill.name}"
                if current_plugin_id == plugin_id:
                    skill_dir = skill.skill_dir or path

                    return RemotePluginInfo(
                        plugin_id=plugin_id,
                        name=skill.name,
                        description=skill.description,
                        version=skill.version,
                        author=skill.author,
                        icon=None,
                        plugin_type="skill",
                        skill_type="knowledge",
                        tags=skill.tags,
                        downloads=None,
                        manifest_url=None,
                        download_url=f"file://{skill_dir}",
                        created_at=None,
                        updated_at=None,
                    )

            return None
        except Exception as e:
            logger.error(f"获取本地 Skill 详情失败: {plugin_id}, 错误: {e}")
            return None

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载插件包

        将 Skill 目录打包为 ZIP 文件，复用 SkillScanner.zip_skill。

        Args:
            config: 市场配置
            plugin_id: 插件ID
            version: 版本号（本地 Skill 忽略此参数）

        Returns:
            tuple[bytes, str]: (插件包数据, SHA256校验和)
        """
        url = config.get("url", "")
        if not url:
            raise ValueError("市场地址不能为空")

        path = self._parse_url(url)
        skills = self.scanner.scan_skills(path)

        # 查找匹配的 Skill
        for skill in skills:
            current_plugin_id = f"{skill.author}/{skill.name}"
            if current_plugin_id == plugin_id:
                return self.scanner.zip_skill(skill)

        raise ValueError(f"Plugin not found: {plugin_id}")

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新

        本地 Skill 不支持更新检查，返回空列表。

        Args:
            config: 市场配置
            plugins: 需要检查的插件列表

        Returns:
            Sequence[PluginUpdateInfo]: 更新信息列表（始终为空）
        """
        return []

    def _parse_url(self, url: str) -> Path:
        """解析 URL 为 Path

        Args:
            url: 文件路径 URL

        Returns:
            Path 对象
        """
        if url.startswith("file://"):
            return Path(url[7:])  # 去掉 "file://" 前缀
        else:
            return Path(url)
