"""本地文件 Plugin 扫描适配器"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class LocalPluginAdapter(MarketplaceAdapter):
    """本地文件 Plugin 扫描适配器

    从本地文件系统扫描 .zip 插件包并返回 Plugin 信息。
    """

    # 缓存：plugin_id -> (zip_path, mtime, parsed_data)
    _cache: dict[str, tuple[Path, float, dict[str, Any]]] = {}

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "local-plugin"

    def _parse_plugin_zip(self, zip_path: Path) -> dict[str, Any]:
        """解析单个插件 ZIP 包

        Args:
            zip_path: ZIP 文件路径

        Returns:
            包含 Plugin 元数据的字典

        Raises:
            ValueError: 包格式无效
        """
        from tenant.services.plugin_package_service import plugin_package_service

        if not zip_path.exists():
            raise ValueError(f"Plugin zip not found: {zip_path}")

        package_data = zip_path.read_bytes()
        package_info = plugin_package_service.parse_package_from_bytes(package_data)

        return {
            "plugin_id": package_info.plugin_id,
            "name": package_info.name,
            "version": package_info.version,
            "author": package_info.author,
            "description": (
                package_info.declaration.get("configuration", {})
                .get("description", {})
                .get("en_US", "")
            ),
            "manifest_type": package_info.manifest_type or "tool",
            "declaration": package_info.declaration,
            "_path": zip_path,
        }

    def _scan_plugins(self, base_dir: Path) -> list[dict[str, Any]]:
        """扫描目录中的所有 .zip 插件包

        Args:
            base_dir: 基础目录路径

        Returns:
            Plugin 元数据列表
        """
        plugins = []

        for zip_file in base_dir.rglob("*.zip"):
            try:
                plugin_data = self._parse_plugin_zip(zip_file)
                plugins.append(plugin_data)
            except ValueError as e:
                logger.warning(f"Failed to parse {zip_file}: {e}")

        return plugins

    def _determine_plugin_type(self, declaration: dict) -> str:
        """从 declaration 推导插件类型

        Args:
            declaration: 插件声明

        Returns:
            插件类型字符串
        """
        models_config = declaration.get("models_configuration", [])
        if models_config and len(models_config) > 0:
            return "model"

        tools_config = declaration.get("tools_configuration", [])
        if tools_config and len(tools_config) > 0:
            return "tool"

        agent_config = declaration.get("agent_strategies_configuration", [])
        if agent_config and len(agent_config) > 0:
            return "agent"

        return "tool"

    def _parse_url(self, url: str) -> Path:
        """解析 URL 为 Path

        Args:
            url: 文件路径 URL

        Returns:
            Path 对象
        """
        if url.startswith("file://"):
            return Path(url[7:])
        return Path(url)

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
            path = self._parse_url(url)

            if not path.exists():
                return MarketplaceTestResult(success=False, message=f"目录不存在: {path}")

            if not path.is_dir():
                return MarketplaceTestResult(success=False, message=f"路径不是目录: {path}")

            plugins = self._scan_plugins(path)

            return MarketplaceTestResult(
                success=True,
                message="连接成功",
                plugin_count=len(plugins),
            )
        except Exception as e:
            logger.error(f"测试本地 Plugin 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取本地插件列表

        Args:
            config: 市场配置
            keyword: 搜索关键词（过滤 name 和 description）
            plugin_type: 插件类型筛选
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
            plugins = self._scan_plugins(path)

            # 过滤关键词
            if keyword:
                keyword_lower = keyword.lower()
                plugins = [
                    p for p in plugins
                    if keyword_lower in p.get("name", "").lower()
                    or keyword_lower in p.get("description", "").lower()
                ]

            # 转换为 RemotePluginInfo
            result = []
            for plugin in plugins:
                plugin_id = plugin["plugin_id"]
                resolved_type = self._determine_plugin_type(plugin.get("declaration", {}))

                # 按类型筛选
                if plugin_type and resolved_type != plugin_type:
                    continue

                result.append(RemotePluginInfo(
                    plugin_id=plugin_id,
                    name=plugin["name"],
                    description=plugin.get("description", ""),
                    version=plugin.get("version", "1.0.0"),
                    author=plugin["author"],
                    icon=None,
                    plugin_type=resolved_type,
                    tags=[],
                    downloads=None,
                    manifest_url=None,
                    download_url=f"file://{plugin['_path']}",
                    created_at=None,
                    updated_at=None,
                ))

            # 分页
            total = len(result)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_plugins = result[start:end]

            return paginated_plugins, total
        except Exception as e:
            logger.error(f"获取本地 Plugin 列表失败: {e}")
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
            plugins = self._scan_plugins(path)

            for plugin in plugins:
                if plugin["plugin_id"] == plugin_id:
                    resolved_type = self._determine_plugin_type(plugin.get("declaration", {}))

                    return RemotePluginInfo(
                        plugin_id=plugin_id,
                        name=plugin["name"],
                        description=plugin.get("description", ""),
                        version=plugin.get("version", "1.0.0"),
                        author=plugin["author"],
                        icon=None,
                        plugin_type=resolved_type,
                        tags=[],
                        downloads=None,
                        manifest_url=None,
                        download_url=f"file://{plugin['_path']}",
                        created_at=None,
                        updated_at=None,
                    )

            return None
        except Exception as e:
            logger.error(f"获取本地 Plugin 详情失败: {plugin_id}, 错误: {e}")
            return None

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载插件包

        读取本地 ZIP 文件。

        Args:
            config: 市场配置
            plugin_id: 插件ID
            version: 版本号（本地 Plugin 忽略此参数）

        Returns:
            tuple[bytes, str]: (插件包数据, SHA256校验和)
        """
        url = config.get("url", "")
        if not url:
            raise ValueError("市场地址不能为空")

        path = self._parse_url(url)
        plugins = self._scan_plugins(path)

        for plugin in plugins:
            if plugin["plugin_id"] == plugin_id:
                zip_path = plugin["_path"]
                zip_data = zip_path.read_bytes()
                checksum = hashlib.sha256(zip_data).hexdigest()
                return zip_data, checksum

        raise ValueError(f"Plugin not found: {plugin_id}")

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新

        本地 Plugin 不支持更新检查，返回空列表。

        Args:
            config: 市场配置
            plugins: 需要检查的插件列表

        Returns:
            Sequence[PluginUpdateInfo]: 更新信息列表（始终为空）
        """
        return []
