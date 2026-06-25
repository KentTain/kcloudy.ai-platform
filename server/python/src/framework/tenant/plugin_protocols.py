"""
插件协议定义

提供插件安装、配置和运行时状态的抽象接口，支持依赖倒置。
Tenant 模块与 AI 模块之间的契约。
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class PluginInstallationDTO:
    """安装记录 DTO"""

    tenant_id: str
    plugin_id: str
    plugin_unique_identifier: str
    status: str = "PENDING"  # PENDING / ACTIVE / INACTIVE / FAILED
    auto_start: bool = False
    freeze_threshold_hours: int = 24
    plugin_type: str | None = None
    runtime_type: str | None = None


@dataclass
class PluginDefinitionDTO:
    """插件定义 DTO"""

    plugin_id: str
    plugin_unique_identifier: str
    install_type: str
    refers: int = 0
    manifest_type: str | None = None
    remote_declaration: dict | None = None


@dataclass
class PluginConfigDTO:
    """AI 侧插件配置 DTO"""

    plugin_id: str
    plugin_config: dict | None = None
    runtime_config: dict | None = None


@dataclass
class PluginRuntimeStateDTO:
    """AI 侧运行时状态 DTO"""

    plugin_id: str
    status: str = "inactive"
    call_count: int = 0
    error_count: int = 0
    process_id: int | None = None
    port: int | None = None
    last_error: str | None = None
    last_started_at: str | None = None
    last_stopped_at: str | None = None
    last_accessed_at: str | None = None
    frozen_at: str | None = None


# ============== PluginInstallationProvider Protocol ==============


class PluginInstallationProvider(Protocol):
    """
    插件安装提供者协议

    抽象租户插件的 CRUD 操作，支持：
    - 本地部署：直接数据库访问
    - 分布式部署：通过 RPC/HTTP 调用 AI 模块
    """

    async def get_tenant_installations(
        self, tenant_id: str
    ) -> list[PluginInstallationDTO]:
        """
        获取租户的所有插件安装记录

        Args:
            tenant_id: 租户 ID

        Returns:
            list[PluginInstallationDTO]
        """
        ...

    async def get_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO | None:
        """
        获取指定插件安装记录

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO | None
        """
        ...

    async def create_installation(
        self, tenant_id: str, data: PluginInstallationDTO
    ) -> PluginInstallationDTO:
        """
        创建插件安装记录

        Args:
            tenant_id: 租户 ID
            data: 安装记录 DTO

        Returns:
            PluginInstallationDTO
        """
        ...

    async def update_installation(
        self, tenant_id: str, plugin_id: str, data: dict
    ) -> PluginInstallationDTO:
        """
        更新插件安装记录

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID
            data: 更新字段字典

        Returns:
            PluginInstallationDTO
        """
        ...

    async def delete_installation(
        self, tenant_id: str, plugin_id: str
    ) -> None:
        """
        删除插件安装记录

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID
        """
        ...


# ============== 全局注册 ==============

_plugin_installation_provider: PluginInstallationProvider | None = None


def register_plugin_installation_provider(
    provider: PluginInstallationProvider,
) -> None:
    """
    注册插件安装提供者

    应用启动时调用，注入具体实现。

    Args:
        provider: PluginInstallationProvider 实现实例
    """
    global _plugin_installation_provider
    _plugin_installation_provider = provider


def get_plugin_installation_provider() -> PluginInstallationProvider:
    """
    获取插件安装提供者

    Returns:
        PluginInstallationProvider 实例

    Raises:
        RuntimeError: 未注册时抛出
    """
    if _plugin_installation_provider is None:
        raise RuntimeError(
            "PluginInstallationProvider not registered. "
            "Call register_plugin_installation_provider() at startup."
        )
    return _plugin_installation_provider
