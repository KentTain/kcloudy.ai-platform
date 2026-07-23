"""
AI 模块客户端

提供对 AI 模块的统一调用入口。
"""

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.plugin_management import (
    BatchInstallResponse,
    InstallationItem,
    StartPluginResponse,
    StopPluginResponse,
)
from framework.clients.inner_http_client import InnerHttpClient


class AIClient:
    """
    AI 模块客户端

    支持单体模式（直接 Service 调用）和微服务模式（HTTP 调用）。
    """

    def __init__(
        self,
        inner_url: str | None = None,
        inner_timeout: float = 30.0,
    ):
        """
        初始化客户端

        Args:
            inner_url: 内部接口 URL（微服务模式）
            inner_timeout: 超时时间（秒）
        """
        self.inner_url = inner_url
        self._http_client: InnerHttpClient | None = None

        if inner_url:
            self._http_client = InnerHttpClient(
                base_url=inner_url,
                timeout=inner_timeout,
                service_name="ai",
                health_path="/ai/inner/v1/health",
            )

    async def start_plugin(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> StartPluginResponse:
        """
        启动插件

        Args:
            session: 数据库会话
            tenant_id: 租户ID
            plugin_id: 插件ID

        Returns:
            StartPluginResponse
        """
        if self._http_client:
            # 微服务模式
            from framework.tenant.context import TenantContext

            TenantContext.set_tenant_id(tenant_id)
            data = await self._http_client.post(
                f"/ai/inner/v1/plugins/{plugin_id}/start",
                json={},
                response_model=StartPluginResponse,
            )
            return data
        else:
            # 单体模式
            from ai.services.plugin import plugin_management_service
            from framework.tenant.context import TenantContext

            TenantContext.set_tenant_id(tenant_id)
            result = await plugin_management_service.start_plugin_with_response(
                session, plugin_id
            )
            return StartPluginResponse(
                plugin_id=result.plugin_id,
                message=result.message,
                status=result.status,
                success=result.success,
                process_id=result.process_id,
                port=result.port,
            )

    async def stop_plugin(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> StopPluginResponse:
        """
        停止插件

        Args:
            session: 数据库会话
            tenant_id: 租户ID
            plugin_id: 插件ID

        Returns:
            StopPluginResponse
        """
        if self._http_client:
            # 微服务模式
            from framework.tenant.context import TenantContext

            TenantContext.set_tenant_id(tenant_id)
            data = await self._http_client.post(
                f"/ai/inner/v1/plugins/{plugin_id}/stop",
                json={},
                response_model=StopPluginResponse,
            )
            return data
        else:
            # 单体模式
            from ai.services.plugin import plugin_management_service
            from framework.tenant.context import TenantContext

            TenantContext.set_tenant_id(tenant_id)
            result = await plugin_management_service.stop_plugin_with_response(
                session, plugin_id
            )
            return StopPluginResponse(
                plugin_id=result.plugin_id,
                message=result.message,
                status=result.status,
                success=result.success,
            )

    async def batch_install_plugins(
        self,
        session: AsyncSession,
        installations: list[InstallationItem],
    ) -> BatchInstallResponse:
        """
        批量安装插件到租户

        Args:
            session: 数据库会话
            installations: 安装项列表

        Returns:
            BatchInstallResponse
        """
        if not installations:
            return BatchInstallResponse(success=[], failed=[], skipped=[])

        if self._http_client:
            # 微服务模式
            data = await self._http_client.post(
                "/ai/inner/v1/plugins/install-batch",
                json={"installations": [item.model_dump() for item in installations]},
                response_model=BatchInstallResponse,
            )
            return data
        else:
            # 单体模式：直接调用 AI Service
            from sqlalchemy import select

            from ai.models.plugin import PluginConfig
            from ai.models.plugin import PluginRuntimeState
            from framework.tenant.context import TenantContext

            success = []
            failed = []
            skipped = []

            for item in installations:
                try:
                    # 设置租户上下文
                    TenantContext.set_tenant_id(item.tenant_id)

                    # 检查是否已存在 PluginConfig
                    stmt = select(PluginConfig).where(
                        PluginConfig.tenant_id == item.tenant_id,
                        PluginConfig.plugin_id == item.plugin_id,
                    )
                    result = await session.execute(stmt)
                    existing_config = result.scalar_one_or_none()

                    if existing_config:
                        skipped.append(
                            {
                                "tenant_id": item.tenant_id,
                                "reason": "already_installed",
                            }
                        )
                        continue

                    # 创建 PluginConfig
                    config = PluginConfig(
                        tenant_id=item.tenant_id,
                        plugin_id=item.plugin_id,
                        plugin_unique_identifier=item.plugin_unique_identifier,
                        plugin_config=item.declaration,
                        runtime_config={},
                    )
                    session.add(config)

                    # 创建 PluginRuntimeState
                    runtime_state = PluginRuntimeState(
                        tenant_id=item.tenant_id,
                        plugin_id=item.plugin_id,
                        status="inactive",
                    )
                    session.add(runtime_state)

                    success.append(
                        {
                            "tenant_id": item.tenant_id,
                            "plugin_id": item.plugin_id,
                        }
                    )

                except Exception as e:
                    failed.append(
                        {
                            "tenant_id": item.tenant_id,
                            "message": str(e),
                        }
                    )

            # 刷新事务
            await session.flush()

            return BatchInstallResponse(
                success=success,
                failed=failed,
                skipped=skipped,
            )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否可用
        """
        if self._http_client:
            return await self._http_client.health_check()
        # 单体模式始终健康
        return True


# 默认客户端实例
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """获取 AI 客户端实例"""
    global _ai_client
    if _ai_client is None:
        from framework.configs import get_settings

        settings = get_settings()
        _ai_client = AIClient(
            inner_url=getattr(settings, "ai_inner_url", None),
            inner_timeout=getattr(settings, "ai_inner_timeout", 30.0),
        )
    return _ai_client
