"""
Tenant 模块的 TenantProvider 实现

本地部署时直接访问数据库获取租户信息。
"""

from loguru import logger

from framework.database.dependencies import get_task_session
from framework.tenant.context import SimpleTenant
from framework.tenant.tenant_protocols import TenantInfo, TenantProvider
from tenant.services.tenant_service import TenantService

_logger = logger.bind(name=__name__)


class TenantProviderImpl(TenantProvider):
    """
    Tenant 模块的 TenantProvider 实现

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
        # 优先从缓存获取（避免创建 session）
        from framework.tenant.cache import TenantCache

        cached = await TenantCache.get(tenant_id)
        if cached and isinstance(cached, SimpleTenant):
            return cached

        # 缓存未命中，查询数据库
        async with get_task_session() as session:
            tenant = await TenantService.get_by_id(session, tenant_id, use_cache=False)
            if tenant and isinstance(tenant, SimpleTenant):
                # 手动写入缓存
                await TenantCache.set(tenant)
                return tenant
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
        from framework.clients.iam_client import get_iam_client

        iam_client = get_iam_client()
        user_tenants = await iam_client.get_user_tenants(user_id)
        if not user_tenants:
            return False

        tenant_ids = [ut.tenant_id for ut in user_tenants]
        return tenant_id in tenant_ids

    async def get_user_tenants(self, user_id: str) -> list[TenantInfo]:
        """
        获取用户所属的租户列表

        Args:
            user_id: 用户 ID

        Returns:
            list[TenantInfo]
        """
        from framework.clients.iam_client import get_iam_client

        iam_client = get_iam_client()
        user_tenants = await iam_client.get_user_tenants(user_id)
        if not user_tenants:
            return []

        # 批量获取租户信息
        tenant_ids = [ut.tenant_id for ut in user_tenants]
        async with get_task_session() as session:
            tenants = await TenantService.get_tenants_batch(session, tenant_ids)

            # 批量构建 SimpleTenant（避免 N+1 查询）
            simple_tenants = await TenantService.build_simple_tenants_batch(
                session, [t for t in tenants if t is not None]
            )
            return simple_tenants


# 单例实例
tenant_provider_impl = TenantProviderImpl()
