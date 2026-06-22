"""
用户模块数据初始化

初始化默认系统管理员用户，关联组织和分配角色。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from framework.module.definition import GLOBAL_ROLES
from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import (
    Organization,
    Role,
    User,
    UserOrganization,
    UserRole,
    UserStatus,
    UserTenant,
)

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

    # 从全局角色定义中获取 sysAdmin 角色编码，避免硬编码
    sysadmin_role_def = next((r for r in GLOBAL_ROLES if r.code == "sysAdmin"), None)
    if not sysadmin_role_def:
        raise ValueError("sysAdmin 角色定义不存在")

    async with get_session() as session:
        # 检查是否已存在默认管理员
        result = await session.execute(
            select(User).where(User.username == DEFAULT_ADMIN_USERNAME).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            write_warning("默认系统管理员已存在，跳过初始化")
            user_id = existing.id
            # 即使跳过用户创建，也要检查并分配角色
            await _ensure_user_role(session, user_id, tenant_id, sysadmin_role_def.code)
            return 0

        # 获取租户实例层的角色 ID（iam.roles 表）
        # 全局角色已通过 sync_module_assigned 同步到租户实例层
        role_result = await session.execute(
            select(Role.id).where(
                Role.tenant_id == tenant_id,
                Role.code == sysadmin_role_def.code,
            )
        )
        role_id = role_result.scalar_one_or_none()

        # 获取默认组织
        org_result = await session.execute(
            select(Organization)
            .where(
                Organization.tenant_id == tenant_id,
                Organization.code == "default",
            )
            .limit(1)
        )
        org = org_result.scalar_one_or_none()

        if dry_run:
            write_info(f"[DRY-RUN] 将创建用户: {DEFAULT_ADMIN_USERNAME}")
            write_info(f"[DRY-RUN] 默认密码: {DEFAULT_ADMIN_PASSWORD}")
            write_info(f"[DRY-RUN] 关联租户: {tenant_id}")
            if role_id:
                write_info(f"[DRY-RUN] 分配角色: {sysadmin_role_def.code}")
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
            write_success(f"分配角色: {sysadmin_role_def.code}")

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

            write_success(f"关联组织: {org.name}")

        await session.commit()

        write_success(f"已创建用户: {user.username}")
        write_success(f"默认密码: {DEFAULT_ADMIN_PASSWORD}")
        write_success(f"关联租户: {tenant_id}")
        write_warning("[WARN] 请在生产环境中修改默认密码!")
        return 1


async def _ensure_user_role(
    session, user_id: str, tenant_id: str, role_code: str
) -> None:
    """
    确保用户拥有指定角色

    检查用户是否已拥有角色，如果没有则分配。

    Args:
        session: 数据库会话
        user_id: 用户 ID
        tenant_id: 租户 ID
        role_code: 角色编码
    """
    # 获取角色 ID
    role_result = await session.execute(
        select(Role.id).where(
            Role.tenant_id == tenant_id,
            Role.code == role_code,
        )
    )
    role_id = role_result.scalar_one_or_none()

    if not role_id:
        write_warning(f"角色不存在: {role_code}，无法分配")
        return

    # 检查用户是否已拥有该角色
    existing_ur = await session.execute(
        select(UserRole).where(
            UserRole.tenant_id == tenant_id,
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
    )
    if existing_ur.scalar_one_or_none():
        write_info(f"用户已拥有角色: {role_code}")
        return

    # 分配角色
    user_role_id = str(uuid.uuid4())
    user_role = UserRole(
        id=user_role_id, user_id=user_id, role_id=role_id, tenant_id=tenant_id
    )
    session.add(user_role)
    await session.commit()
    write_success(f"分配角色: {role_code}")
