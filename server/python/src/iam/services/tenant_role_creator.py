"""
租户角色创建器实现

为租户自动创建 owner/admin/member 角色。
"""

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Permission, Role, RolePermission, UserRole

_logger = logger.bind(name=__name__)


class IAMTenantRoleCreator:
    """IAM 租户角色创建器"""

    async def create_roles(
        self,
        session: AsyncSession,
        tenant_id: str,
        creator_user_id: str | None = None,
    ) -> None:
        """
        为租户创建默认角色

        创建 owner/admin/member 三个租户级角色，并分配相应权限。
        如果提供了 creator_user_id，自动为其分配 owner 角色。

        Args:
            session: 当前数据库会话
            tenant_id: 租户 ID
            creator_user_id: 创建者用户 ID（用于自动分配 owner 角色）
        """
        # 定义角色
        roles_to_create = [
            {
                "code": f"{tenant_id}:owner",
                "name": "租户所有者",
                "description": "拥有租户的所有权限",
            },
            {
                "code": f"{tenant_id}:admin",
                "name": "租户管理员",
                "description": "拥有租户的管理权限",
            },
            {
                "code": f"{tenant_id}:member",
                "name": "租户成员",
                "description": "拥有租户的基础访问权限",
            },
        ]

        created_roles: dict[str, Role] = {}
        for role_def in roles_to_create:
            # 幂等检查
            existing = await session.execute(
                select(Role).where(
                    Role.tenant_id == tenant_id,
                    Role.code == role_def["code"],
                )
            )
            if existing.scalar_one_or_none():
                _logger.debug(f"角色已存在: {role_def['code']}")
                continue

            role = Role(
                tenant_id=tenant_id,
                code=role_def["code"],
                name=role_def["name"],
                description=role_def["description"],
                is_system=False,
            )
            session.add(role)
            await session.flush()
            created_roles[role_def["code"]] = role
            _logger.info(f"创建租户角色: {role_def['code']}")

        # 获取租户的所有权限（从已分配模块同步过来的）
        perms_result = await session.execute(
            select(Permission).where(Permission.tenant_id == tenant_id)
        )
        tenant_permissions = list(perms_result.scalars().all())

        # 为 owner 分配所有权限
        owner_role = created_roles.get(f"{tenant_id}:owner")
        if owner_role and tenant_permissions:
            for perm in tenant_permissions:
                # 幂等检查
                existing_rp = await session.execute(
                    select(RolePermission).where(
                        RolePermission.tenant_id == tenant_id,
                        RolePermission.role_id == owner_role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if existing_rp.scalar_one_or_none():
                    continue
                rp = RolePermission(
                    tenant_id=tenant_id,
                    role_id=owner_role.id,
                    permission_id=perm.id,
                )
                session.add(rp)
            _logger.info(f"为 owner 分配权限: {len(tenant_permissions)} 个")

        # 为创建者分配 owner 角色
        if creator_user_id and owner_role:
            existing_ur = await session.execute(
                select(UserRole).where(
                    UserRole.tenant_id == tenant_id,
                    UserRole.user_id == creator_user_id,
                    UserRole.role_id == owner_role.id,
                )
            )
            if not existing_ur.scalar_one_or_none():
                user_role = UserRole(
                    tenant_id=tenant_id,
                    user_id=creator_user_id,
                    role_id=owner_role.id,
                )
                session.add(user_role)
                _logger.info(f"创建者获得 owner 角色: user_id={creator_user_id}")

        _logger.info(f"租户角色创建完成: tenant_id={tenant_id}")
