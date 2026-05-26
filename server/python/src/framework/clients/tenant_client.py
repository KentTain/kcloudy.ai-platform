"""
Tenant 客户端

提供对 Tenant 模块的统一调用入口。
"""

from typing import Any

from pydantic import BaseModel, Field

from framework.clients.inner_http_client import InnerHttpClient


class TenantInfo(BaseModel):
    """租户信息"""
    id: str = Field(..., description="租户ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    status: str = Field(..., description="状态")


class TenantClient:
    """
    Tenant 模块客户端

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
                service_name="tenant",
                health_path="/inner/v1/tenant/health",
            )

    async def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        """
        获取单个租户

        Args:
            tenant_id: 租户 ID

        Returns:
            TenantInfo | None
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/inner/v1/tenants/{tenant_id}",
                response_model=TenantInfo,
            )
            return data
        else:
            # 单体模式：直接调用 Service
            from tenant.services.tenant_service import TenantService
            from framework.tenant.context import SimpleTenant

            tenant = await TenantService.get_by_id(tenant_id)
            if tenant:
                if isinstance(tenant, SimpleTenant):
                    return TenantInfo(
                        id=tenant.id,
                        name=tenant.name,
                        code=tenant.code,
                        status=tenant.status,
                    )
                return TenantInfo(
                    id=tenant.id,
                    name=tenant.name,
                    code=tenant.code,
                    status=tenant.status,
                )
            return None

    async def get_tenants_batch(self, tenant_ids: list[str]) -> list[TenantInfo]:
        """
        批量获取租户

        Args:
            tenant_ids: 租户 ID 列表

        Returns:
            list[TenantInfo]
        """
        if not tenant_ids:
            return []

        if self._http_client:
            # 微服务模式
            from pydantic import BaseModel
            from typing import Any

            class BatchResponse(BaseModel):
                items: list[TenantInfo]

            data = await self._http_client.post(
                "/inner/v1/tenants/batch",
                json={"tenant_ids": tenant_ids},
            )
            if data and isinstance(data, list):
                return [TenantInfo.model_validate(item) for item in data]
            return []
        else:
            # 单体模式
            from tenant.services.tenant_service import TenantService

            tenants = await TenantService.get_tenants_batch(tenant_ids)
            return [
                TenantInfo(
                    id=t.id,
                    name=t.name,
                    code=t.code,
                    status=t.status,
                )
                for t in tenants if t
            ]

    async def validate_access(self, user_id: str, tenant_id: str) -> bool:
        """
        验证用户是否有权访问租户

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID

        Returns:
            bool
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/inner/v1/tenants/{tenant_id}/validate",
            )
            if data and isinstance(data, dict):
                return data.get("valid", False)
            return False
        else:
            # 单体模式
            from iam.models import UserTenant
            from framework.database.core.engine import async_session
            from sqlalchemy import select

            async with async_session() as session:
                stmt = select(UserTenant).where(
                    UserTenant.user_id == user_id,
                    UserTenant.tenant_id == tenant_id,
                )
                result = await session.execute(stmt)
                user_tenant = result.scalar_one_or_none()
                return user_tenant is not None

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
_tenant_client: TenantClient | None = None


def get_tenant_client() -> TenantClient:
    """获取 Tenant 客户端实例"""
    global _tenant_client
    if _tenant_client is None:
        from framework.configs import get_settings
        settings = get_settings()
        _tenant_client = TenantClient(
            inner_url=getattr(settings, "tenant_inner_url", None),
            inner_timeout=getattr(settings, "tenant_inner_timeout", 30.0),
        )
    return _tenant_client
