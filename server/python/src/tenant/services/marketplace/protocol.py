"""插件市场适配器协议"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class RemotePluginInfo:
    """远程插件信息"""

    plugin_id: str  # 插件ID：author/name
    name: str  # 显示名称
    description: str | None  # 描述
    version: str  # 版本
    author: str  # 作者
    icon: str | None  # 图标 URL
    plugin_type: str  # tool/model/agent/skill
    manifest_url: str | None  # 清单文件 URL
    download_url: str  # 下载地址
    created_at: datetime | None
    updated_at: datetime | None
    skill_type: str | None = None  # Skill 类型：knowledge(知识文档) | script(简单脚本)
    skill_metadata: dict | None = None  # Skill 特有元数据
    tags: list[str] = field(default_factory=list)  # 标签
    downloads: int | None = None  # 下载量


@dataclass
class PluginUpdateInfo:
    """插件更新信息"""

    plugin_id: str
    current_version: str  # 当前版本
    latest_version: str  # 最新版本
    has_update: bool  # 是否有更新
    changelog: str | None  # 更新日志


@dataclass
class MarketplaceTestResult:
    """市场连接测试结果"""

    success: bool
    message: str
    plugin_count: int | None = None  # 可用插件数量
    latency_ms: int | None = None  # 响应延迟


class MarketplaceAdapter(Protocol):
    """市场适配器协议"""

    @property
    def market_type(self) -> str:
        """市场类型标识：dify, modelscope"""
        ...

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接

        Args:
            config: 市场配置（url, auth_type, auth_config）

        Returns:
            MarketplaceTestResult: 测试结果
        """
        ...

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
            keyword: 搜索关键词
            plugin_type: 插件类型筛选
            page: 页码
            page_size: 每页条数

        Returns:
            tuple[Sequence[RemotePluginInfo], int]: (插件列表, 总数)
        """
        ...

    async def get_plugin(
        self,
        config: dict,
        plugin_id: str,
    ) -> RemotePluginInfo | None:
        """获取单个插件详情

        Args:
            config: 市场配置
            plugin_id: 插件ID

        Returns:
            RemotePluginInfo | None: 插件信息，不存在返回 None
        """
        ...

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载插件包

        Args:
            config: 市场配置
            plugin_id: 插件ID
            version: 版本号，None 表示最新版本

        Returns:
            tuple[bytes, str]: (插件包数据, SHA256校验和)
        """
        ...

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查插件更新

        Args:
            config: 市场配置
            plugins: 需要检查的插件列表，每项包含 plugin_id, current_version

        Returns:
            Sequence[PluginUpdateInfo]: 更新信息列表
        """
        ...
