"""
IAM 模块的 TenantProvider 实现

本地部署时直接访问数据库获取租户信息。
"""

from sqlalchemy import select

from framework.database.core.engine import async_session
from framework.tenant.context import SimpleTenant
from framework.tenant.protocols import TenantInfo, TenantProvider
from iam.models import UserTenant
from iam.services.tenant_service import TenantService


class IamTenantProvider(TenantProvider):
    """
    IAM 模块的 TenantProvider 实现

    本地部署时直接访问数据库。
    """

    async def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        """
        获取租户信息

        Args:
            tenant_id: 租户 ID

        Returns:
            TenantInfo | None
        """
        tenant = await TenantService.get_by_id(tenant_id)
        if tenant:
            return SimpleTenant.from_model(tenant)
        return None

    async def validate_access(self, user_id: str, tenant_id: str) -> bool:
        """
        验证用户是否有权访问租户

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID

        Returns:
            bool
        """
        async with async_session() as session:
            stmt = select(UserTenant).where(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            user_tenant = result.scalar_one_or_none()
            return user_tenant is not None

    async def get_user_tenants(self, user_id: str) -> list[TenantInfo]:
        """
        获取用户所属的租户列表

        Args:
            user_id: 用户 ID

        Returns:
            list[TenantInfo]
        """
        tenants = await TenantService.get_user_tenants(user_id)
        return [SimpleTenant.from_model(t) for t in tenants]


# 单例实例
iam_tenant_provider = IamTenantProvider()
