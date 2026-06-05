"""
用户模块数据初始化

初始化默认系统管理员用户。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, text

from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import User, UserRole, UserStatus, UserTenant

# 默认系统管理员配置
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_EMAIL = "admin@example.com"


async def run(*, dry_run: bool = False) -> int:
    """初始化用户数据

    创建默认系统管理员用户并关联到默认租户。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session
    from framework.utils.crypto import hash_password

    async with get_session() as session:
        # 检查是否已存在默认管理员
        result = await session.execute(
            select(User).where(User.username == DEFAULT_ADMIN_USERNAME).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            write_info("    默认系统管理员已存在，跳过初始化")
            return 0

        # 获取默认租户 ID
        tenant_result = await session.execute(
            text("SELECT id FROM tenant.tenants WHERE code = 'default' LIMIT 1")
        )
        tenant_row = tenant_result.fetchone()
        if not tenant_row:
            write_warning("    [WARN] 默认租户不存在，跳过创建系统管理员")
            write_warning("    [HINT] 请先运行 tenant seed 创建默认租户")
            return 0

        tenant_id = tenant_row[0]

        # 获取系统管理员角色 ID
        role_result = await session.execute(
            text("SELECT id FROM iam.roles WHERE code = 'system_admin' LIMIT 1")
        )
        role_row = role_result.fetchone()
        role_id = role_row[0] if role_row else None

        if dry_run:
            write_info(f"    [DRY-RUN] 将创建用户: {DEFAULT_ADMIN_USERNAME}")
            write_info(f"    [DRY-RUN] 默认密码: {DEFAULT_ADMIN_PASSWORD}")
            write_info(f"    [DRY-RUN] 关联租户: {tenant_id}")
            if role_id:
                write_info(f"    [DRY-RUN] 分配角色: system_admin")
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
        )
        session.add(user)

        # 立即 flush 确保用户被写入数据库
        await session.flush()

        # 创建用户-租户关联
        user_tenant_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO iam.user_tenants (id, user_id, tenant_id, is_default, role, created_at, updated_at)
                VALUES (:id, :user_id, :tenant_id, true, 'admin', now(), now())
            """),
            {"id": user_tenant_id, "user_id": user_id, "tenant_id": tenant_id},
        )

        # 分配系统管理员角色
        if role_id:
            user_role_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO iam.user_roles (id, user_id, role_id, created_at, updated_at)
                    VALUES (:id, :user_id, :role_id, now(), now())
                """),
                {"id": user_role_id, "user_id": user_id, "role_id": role_id},
            )

        await session.commit()

        write_success(f"    已创建用户: {user.username}")
        write_success(f"    默认密码: {DEFAULT_ADMIN_PASSWORD}")
        write_success(f"    关联租户: {tenant_id}")
        if role_id:
            write_success(f"    分配角色: system_admin")
        write_warning("    [WARN] 请在生产环境中修改默认密码!")
        return 1
