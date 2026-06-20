"""
用户模块数据初始化

初始化默认系统管理员用户，关联组织和分配角色。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import Organization, User, UserOrganization, UserRole, UserStatus, UserTenant
from tenant.models import ModuleRole

# 默认系统管理员配置
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_EMAIL = "admin@example.com"


async def run(*, dry_run: bool = False) -> int:
    """初始化用户数据

    创建默认系统管理员用户并关联到默认租户、组织和角色。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session
    from framework.utils.crypto import hash_password

    settings = get_settings()
    tenant_config = settings.tenant
    tenant_id = tenant_config.default_tenant_id

    async with get_session() as session:
        # 检查是否已存在默认管理员
        result = await session.execute(
            select(User).where(User.username == DEFAULT_ADMIN_USERNAME).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            write_warning("默认系统管理员已存在，跳过初始化")
            return 0

        # 获取全局角色 ID（通过 code="sysAdmin" 查找）
        role_result = await session.execute(
            select(ModuleRole.id).where(
                ModuleRole.module_id.is_(None),
                ModuleRole.code == "sysAdmin",
            )
        )
        role_id = role_result.scalar_one_or_none()

        # 获取默认组织
        org_result = await session.execute(
            select(Organization).where(
                Organization.tenant_id == tenant_id,
                Organization.code == "default",
            ).limit(1)
        )
        org = org_result.scalar_one_or_none()

        if dry_run:
            write_info(f"[DRY-RUN] 将创建用户: {DEFAULT_ADMIN_USERNAME}")
            write_info(f"[DRY-RUN] 默认密码: {DEFAULT_ADMIN_PASSWORD}")
            write_info(f"[DRY-RUN] 关联租户: {tenant_id}")
            if role_id:
                write_info("[DRY-RUN] 分配角色: sysAdmin")
            if org:
                write_info(f"[DRY-RUN] 关联组织: {org.name}")
            return 1

        # 创建用户
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            email=DEFAULT_ADMIN_EMAIL,
            nickname="系统管理员",
            status=UserStatus.ACTIVE,
            profile_completed=True,
            is_email_verified=True,
            tenant_id=tenant_id,
        )
        session.add(user)

        # 立即 flush 确保用户被写入数据库
        await session.flush()

        # 创建用户-租户关联（设置 is_default=True 作为用户的默认租户）
        user_tenant_id = str(uuid.uuid4())
        userTenant = UserTenant(
            id=user_tenant_id, user_id=user_id, tenant_id=tenant_id, is_default=True
        )
        session.add(userTenant)
        await session.flush()

        # 分配系统管理员角色
        if role_id:
            user_role_id = str(uuid.uuid4())
            userRole = UserRole(
                id=user_role_id, user_id=user_id, role_id=role_id, tenant_id=tenant_id
            )
            session.add(userRole)
            await session.flush()
            write_success("    分配角色: sysAdmin")

        # 创建用户-组织关联
        if org:
            user_org_id = str(uuid.uuid4())
            userOrg = UserOrganization(
                id=user_org_id,
                user_id=user_id,
                organization_id=org.id,
                is_leader=True,
                tenant_id=tenant_id,
            )
            session.add(userOrg)
            await session.flush()

            # 更新组织负责人
            org.leader_id = user_id
            await session.flush()

            write_success(f"    关联组织: {org.name}")

        await session.commit()

        write_success(f"    已创建用户: {user.username}")
        write_success(f"    默认密码: {DEFAULT_ADMIN_PASSWORD}")
        write_success(f"    关联租户: {tenant_id}")
        write_warning("    [WARN] 请在生产环境中修改默认密码!")
        return 1
