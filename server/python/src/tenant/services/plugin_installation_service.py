"""
插件安装管理 Service

提供插件启停操作的业务逻辑：
- 单个启动/停止
- 批量启动/停止（一个插件 → 多租户）
- 前置校验（安装记录、状态、插件定义启用状态）
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from framework.tenant.plugin_protocols import (
    PluginInstallationDTO,
    get_plugin_installation_provider,
)
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation
from tenant.schemas.plugin import (
    BatchOperationFailedItem,
    BatchOperationItem,
    BatchStartStopRequest,
    BatchStartStopResponse,
)

_logger = logger.bind(name=__name__)


class PluginInstallationService:
    """插件安装管理 Service"""

    async def start_plugin(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        启动租户插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在、状态不允许启动、插件定义已禁用
            RuntimeError: 插件启动失败
        """
        # 1. 校验安装记录存在且状态为 INACTIVE
        installation = await TenantPluginInstallation.first_by_fields(
            session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
        )
        if not installation:
            raise ValueError(f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}")

        if installation.status != "INACTIVE":
            raise ValueError(f"插件状态不允许启动: 当前状态={installation.status}，需要 INACTIVE")

        # 2. 校验插件定义为启用状态
        definition = await TenantPluginDefinition.one_by_field(
            session, "plugin_id", plugin_id
        )
        if definition and not definition.is_enabled:
            raise ValueError(f"插件定义已禁用: {plugin_id}")

        # 3. 调用 Provider 启动
        provider = get_plugin_installation_provider()
        result = await provider.start_installation(tenant_id, plugin_id)

        _logger.info(f"插件启动成功: tenant_id={tenant_id}, plugin_id={plugin_id}")
        return result

    async def stop_plugin(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        停止租户插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在、状态不允许停止
            RuntimeError: 插件停止失败
        """
        # 1. 校验安装记录存在且状态为 ACTIVE
        installation = await TenantPluginInstallation.first_by_fields(
            session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
        )
        if not installation:
            raise ValueError(f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}")

        if installation.status != "ACTIVE":
            raise ValueError(f"插件状态不允许停止: 当前状态={installation.status}，需要 ACTIVE")

        # 2. 调用 Provider 停止
        provider = get_plugin_installation_provider()
        result = await provider.stop_installation(tenant_id, plugin_id)

        _logger.info(f"插件停止成功: tenant_id={tenant_id}, plugin_id={plugin_id}")
        return result

    async def batch_start_plugins(
        self, session: AsyncSession, request: BatchStartStopRequest
    ) -> BatchStartStopResponse:
        """
        批量启动插件（一个插件 → 多租户）

        Args:
            session: 数据库会话
            request: 批量启停请求

        Returns:
            BatchStartStopResponse
        """
        success: list[BatchOperationItem] = []
        failed: list[BatchOperationFailedItem] = []

        for tenant_id in request.tenant_ids:
            try:
                result = await self.start_plugin(session, tenant_id, request.plugin_id)
                success.append(
                    BatchOperationItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        status=result.status,
                    )
                )
            except Exception as e:
                _logger.warning(
                    f"批量启动插件失败: tenant_id={tenant_id}, "
                    f"plugin_id={request.plugin_id}, error={str(e)}"
                )
                failed.append(
                    BatchOperationFailedItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        error=str(e),
                    )
                )

        return BatchStartStopResponse(success=success, failed=failed)

    async def batch_stop_plugins(
        self, session: AsyncSession, request: BatchStartStopRequest
    ) -> BatchStartStopResponse:
        """
        批量停止插件（一个插件 → 多租户）

        Args:
            session: 数据库会话
            request: 批量启停请求

        Returns:
            BatchStartStopResponse
        """
        success: list[BatchOperationItem] = []
        failed: list[BatchOperationFailedItem] = []

        for tenant_id in request.tenant_ids:
            try:
                result = await self.stop_plugin(session, tenant_id, request.plugin_id)
                success.append(
                    BatchOperationItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        status=result.status,
                    )
                )
            except Exception as e:
                _logger.warning(
                    f"批量停止插件失败: tenant_id={tenant_id}, "
                    f"plugin_id={request.plugin_id}, error={str(e)}"
                )
                failed.append(
                    BatchOperationFailedItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        error=str(e),
                    )
                )

        return BatchStartStopResponse(success=success, failed=failed)


# 单例实例
plugin_installation_service = PluginInstallationService()
