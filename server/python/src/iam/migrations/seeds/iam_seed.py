"""
IAM 模块数据初始化

初始化预定义角色和权限。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from iam.models import Permission, Role


# 预定义权限
DEFAULT_PERMISSIONS = [
    # 用户权限
    {"code": "user:read", "name": "查看用户", "resource": "user", "action": "read"},
    {"code": "user:write", "name": "编辑用户", "resource": "user", "action": "write"},
    {"code": "user:delete", "name": "删除用户", "resource": "user", "action": "delete"},
    # 角色权限
    {"code": "role:read", "name": "查看角色", "resource": "role", "action": "read"},
    {"code": "role:write", "name": "编辑角色", "resource": "role", "action": "write"},
    {"code": "role:delete", "name": "删除角色", "resource": "role", "action": "delete"},
    # 部门权限
    {"code": "department:read", "name": "查看部门", "resource": "department", "action": "read"},
    {"code": "department:write", "name": "编辑部门", "resource": "department", "action": "write"},
    {"code": "department:delete", "name": "删除部门", "resource": "department", "action": "delete"},
    # 租户权限
    {"code": "tenant:read", "name": "查看租户", "resource": "tenant", "action": "read"},
    {"code": "tenant:write", "name": "编辑租户", "resource": "tenant", "action": "write"},
    {"code": "tenant:delete", "name": "删除租户", "resource": "tenant", "action": "delete"},
    # 权限管理
    {"code": "permission:read", "name": "查看权限", "resource": "permission", "action": "read"},
]


# 预定义角色及其权限
DEFAULT_ROLES = {
    "tenant_admin": {
        "name": "租户管理员",
        "description": "系统最高权限，可创建租户和管理租户管理员",
        "permissions": ["tenant:read", "tenant:write", "tenant:delete", "user:*", "role:*", "department:*"],
    },
    "system_admin": {
        "name": "系统管理员",
        "description": "租户内最高权限，可管理本租户的用户、角色、权限",
        "permissions": ["user:*", "role:*", "department:*", "permission:read"],
    },
    "user": {
        "name": "普通用户",
        "description": "普通业务用户",
        "permissions": ["user:read"],
    },
}


async def run(*, dry_run: bool = False) -> int:
    """初始化 IAM 数据

    创建预定义角色和权限。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session

    async with get_session() as session:
        created_count = 0

        # 1. 创建权限
        existing_perms = set()
        result = await session.execute(select(Permission.code))
        for row in result.scalars():
            existing_perms.add(row)

        permissions_to_create = []
        for perm_data in DEFAULT_PERMISSIONS:
            if perm_data["code"] not in existing_perms:
                perm = Permission(
                    id=str(uuid.uuid4()),
                    **perm_data,
                )
                permissions_to_create.append(perm)
                created_count += 1

        if dry_run:
            for perm in permissions_to_create:
                print(f"    [DRY-RUN] 将创建权限: {perm.code} - {perm.name}")
        else:
            for perm in permissions_to_create:
                session.add(perm)
                print(f"    已创建权限: {perm.code}")

        # 2. 创建角色
        existing_roles = set()
        result = await session.execute(select(Role.code))
        for row in result.scalars():
            existing_roles.add(row)

        roles_to_create = []
        for role_code, role_data in DEFAULT_ROLES.items():
            if role_code not in existing_roles:
                role = Role(
                    id=str(uuid.uuid4()),
                    tenant_id=None,  # 全局角色
                    code=role_code,
                    name=role_data["name"],
                    description=role_data["description"],
                    is_system=True,  # 系统内置角色不可删除
                )
                roles_to_create.append((role, role_data["permissions"]))
                created_count += 1

        if dry_run:
            for role, _ in roles_to_create:
                print(f"    [DRY-RUN] 将创建角色: {role.code} - {role.name}")
        else:
            # 获取所有权限用于关联
            all_permissions = {}
            result = await session.execute(select(Permission))
            for perm in result.scalars():
                all_permissions[perm.code] = perm

            for role, perm_codes in roles_to_create:
                session.add(role)
                await session.flush()

                # 关联权限（支持通配符）
                from iam.models import RolePermission

                for perm_code in perm_codes:
                    if perm_code.endswith(":*"):
                        # 通配符权限：匹配所有相关权限
                        resource = perm_code[:-2]
                        for p_code, perm in all_permissions.items():
                            if p_code.startswith(f"{resource}:"):
                                rp = RolePermission(
                                    id=str(uuid.uuid4()),
                                    role_id=role.id,
                                    permission_id=perm.id,
                                )
                                session.add(rp)
                    elif perm_code in all_permissions:
                        rp = RolePermission(
                            id=str(uuid.uuid4()),
                            role_id=role.id,
                            permission_id=all_permissions[perm_code].id,
                        )
                        session.add(rp)

                print(f"    已创建角色: {role.code}")

            await session.commit()

        return created_count
