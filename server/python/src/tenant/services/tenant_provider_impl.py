"""
Tenant 模块的 TenantProvider 实现

本地部署时直接访问数据库获取租户信息。
"""

from loguru import logger
from sqlalchemy import select

from framework.database.core.engine import async_session
from framework.tenant.context import SimpleTenant
from framework.tenant.protocols import TenantInfo, TenantProvider
from framework.utils.crypto import decrypt
from tenant.models import Tenant
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
        tenant = await TenantService.get_by_id(tenant_id)
        if tenant:
            return self._build_tenant_info(tenant)
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
        tenants = await TenantService.get_tenants_batch(tenant_ids)
        return [self._build_tenant_info(t) for t in tenants]

    def _build_tenant_info(self, tenant: Tenant | SimpleTenant) -> SimpleTenant:
        """
        构建租户信息，包含资源配置

        Args:
            tenant: Tenant ORM 模型或缓存中的 SimpleTenant

        Returns:
            SimpleTenant
        """
        if isinstance(tenant, SimpleTenant):
            return tenant

        # 从模型创建基础信息
        simple_tenant = SimpleTenant.from_model(tenant)

        db_name = getattr(tenant, "db_name", None)
        db_password = getattr(tenant, "db_password", None)
        if (
            isinstance(db_name, str)
            and db_name
            and isinstance(db_password, str)
            and db_password
        ):
            try:
                decrypted_password = decrypt(db_password)
                # 更新数据库配置中的密码
                if simple_tenant.database:
                    simple_tenant.database.password = decrypted_password
            except Exception as e:
                _logger.warning(
                    f"解密租户 {tenant.id} 数据库密码失败: {e}，密码将保持为空"
                )
                # 解密失败，密码保持为空

        return simple_tenant


# 单例实例
tenant_provider_impl = TenantProviderImpl()
