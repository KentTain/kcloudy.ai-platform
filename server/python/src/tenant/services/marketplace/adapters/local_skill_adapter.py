"""本地文件 Skill 扫描适配器"""

from __future__ import annotations

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class LocalSkillAdapter(MarketplaceAdapter):
    """本地文件 Skill 扫描适配器

    从本地文件系统扫描 SKILL.md 文件并返回 Skill 信息。
    支持递归扫描目录，解析 YAML front matter。
    """

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "local-skill"

    def _parse_skill_file(self, skill_file: Path) -> dict[str, Any]:
        """解析 SKILL.md 文件，提取元数据

        Args:
            skill_file: SKILL.md 文件路径

        Returns:
            包含 Skill 元数据的字典

        Raises:
            ValueError: 文件格式无效
        """
        if not skill_file.exists():
            raise ValueError(f"Skill file not found: {skill_file}")

        content = skill_file.read_text(encoding="utf-8")

        # 检查是否以 --- 开头
        if not content.startswith("---"):
            raise ValueError("Invalid SKILL.md format: missing front matter delimiter")

        # 提取 front matter
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid SKILL.md format: malformed front matter")

        front_matter_text = parts[1].strip()

        try:
            front_matter = yaml.safe_load(front_matter_text)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid SKILL.md format: YAML parse error: {e}") from e

        if not isinstance(front_matter, dict):
            raise ValueError("Invalid SKILL.md format: front matter must be a YAML map")

        # 提取必需字段
        name = front_matter.get("name")
        if not name:
            raise ValueError("Invalid SKILL.md format: missing 'name' field")

        # 提取可选字段，设置默认值
        author = front_matter.get("author", "local")
        version = front_matter.get("version", "1.0.0")
        description = front_matter.get("description", "")

        # 提取 tags
        tags = []
        metadata = front_matter.get("metadata", {})
        if isinstance(metadata, dict):
            hermes = metadata.get("hermes", {})
            if isinstance(hermes, dict):
                tags = hermes.get("tags", [])

        return {
            "name": name,
            "description": description,
            "version": version,
            "author": author,
            "tags": tags if isinstance(tags, list) else [],
        }

    def _scan_skills(self, base_dir: Path) -> list[dict[str, Any]]:
        """扫描目录中的所有 SKILL.md 文件

        Args:
            base_dir: 基础目录路径

        Returns:
            Skill 元数据列表
        """
        skills = []

        # 递归查找所有 SKILL.md 文件
        for skill_file in base_dir.rglob("SKILL.md"):
            try:
                skill_data = self._parse_skill_file(skill_file)
                skill_data["_path"] = skill_file.parent
                skills.append(skill_data)
            except ValueError as e:
                logger.warning(f"Failed to parse {skill_file}: {e}")

        return skills

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
            skills = self._scan_skills(path)

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
            skills = self._scan_skills(path)

            # 过滤关键词
            if keyword:
                keyword_lower = keyword.lower()
                skills = [
                    s for s in skills
                    if keyword_lower in s.get("name", "").lower()
                    or keyword_lower in s.get("description", "").lower()
                ]

            # 转换为 RemotePluginInfo
            plugins = []
            for skill in skills:
                skill_dir = skill.get("_path", path)
                plugin_id = f"{skill['author']}/{skill['name']}"

                plugins.append(RemotePluginInfo(
                    plugin_id=plugin_id,
                    name=skill["name"],
                    description=skill.get("description", ""),
                    version=skill.get("version", "1.0.0"),
                    author=skill["author"],
                    icon=None,
                    plugin_type="skill",
                    skill_type="knowledge",  # 默认为知识文档
                    tags=skill.get("tags", []),
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
            skills = self._scan_skills(path)

            # 查找匹配的 Skill
            for skill in skills:
                current_plugin_id = f"{skill['author']}/{skill['name']}"
                if current_plugin_id == plugin_id:
                    skill_dir = skill.get("_path", path)

                    return RemotePluginInfo(
                        plugin_id=plugin_id,
                        name=skill["name"],
                        description=skill.get("description", ""),
                        version=skill.get("version", "1.0.0"),
                        author=skill["author"],
                        icon=None,
                        plugin_type="skill",
                        skill_type="knowledge",
                        tags=skill.get("tags", []),
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

        将 Skill 目录打包为 ZIP 文件。

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
        skills = self._scan_skills(path)

        # 查找匹配的 Skill
        for skill in skills:
            current_plugin_id = f"{skill['author']}/{skill['name']}"
            if current_plugin_id == plugin_id:
                skill_dir = skill.get("_path", path)

                # 打包为 ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in skill_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(skill_dir)
                            zipf.write(file_path, arcname)

                zip_data = zip_buffer.getvalue()
                checksum = hashlib.sha256(zip_data).hexdigest()

                return zip_data, checksum

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
