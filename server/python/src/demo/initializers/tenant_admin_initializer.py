"""
租户管理员初始化器

系统启动时自动创建默认租户管理员。
"""

from loguru import logger
from sqlalchemy import select

from demo.models.tenant import TenantAdmin
from framework.database.core.engine import async_session
from demo.middlewares.admin_auth_middleware import hash_password

_logger = logger.bind(name=__name__)

# 默认管理员配置
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"  # 生产环境应从配置读取


class TenantAdminInitializer:
    """
    租户管理员初始化器

    场景：首次启动创建默认管理员
    WHEN 系统首次启动且不存在默认租户管理员
    THEN 自动创建默认租户管理员

    场景：已存在默认管理员时跳过
    WHEN 系统启动时已存在默认租户管理员
    THEN 跳过创建
    """

    @staticmethod
    async def init() -> TenantAdmin | None:
        """
        初始化默认租户管理员

        Returns:
            TenantAdmin | None: 创建或已存在的管理员
        """
        async with async_session() as session:
            # 检查是否已存在默认管理员
            stmt = select(TenantAdmin).where(TenantAdmin.is_default == True)
            result = await session.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                _logger.info(f"默认租户管理员已存在: {existing_admin.username}")
                return existing_admin

            # 创建默认管理员
            admin = TenantAdmin(
                username=DEFAULT_ADMIN_USERNAME,
                password=hash_password(DEFAULT_ADMIN_PASSWORD),
                is_default=True,
                is_active=True,
            )

            session.add(admin)
            await session.commit()
            await session.refresh(admin)

            _logger.info(
                f"默认租户管理员创建成功: {admin.username} "
                f"(请及时修改默认密码)"
            )

            return admin

    @staticmethod
    async def check_initialized() -> bool:
        """检查是否已初始化"""
        async with async_session() as session:
            stmt = select(TenantAdmin).where(TenantAdmin.is_default == True)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None


async def init_tenant_admin() -> TenantAdmin | None:
    """初始化租户管理员（便捷函数）"""
    return await TenantAdminInitializer.init()
