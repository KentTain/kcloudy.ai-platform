"""权限配置服务（权限组 + 资源 ACL）"""

import copy

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import LibraryRole, LibraryRoleMember, ResourceAcl
from document.models.enums import LibraryRoleKind, ResourceAclEffect, ResourceAclStatus
from framework.common.ctx import get_tenant_id, get_user_id


class PermissionConfigService:
    """权限配置服务"""

    # ==================== 权限组 ====================

    @staticmethod
    async def list_roles(
        session: AsyncSession,
        library_id: str,
    ) -> list[LibraryRole]:
        """查询文档库权限组列表"""
        tenant_id = get_tenant_id()
        stmt = (
            select(LibraryRole)
            .where(LibraryRole.library_id == library_id, LibraryRole.tenant_id == tenant_id, LibraryRole.status == "active")
            .order_by(LibraryRole.role_kind, LibraryRole.created_at)
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def create_role(
        session: AsyncSession,
        library_id: str,
        code: str,
        name: str,
        description: str | None = None,
    ) -> LibraryRole:
        """创建权限组（新建权限组默认复制全员权限）"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        # 获取全员权限组的权限定义，复制到新权限组
        all_members_role = await PermissionConfigService._get_all_members_role(session, library_id)
        default_permissions = copy.deepcopy(all_members_role.permissions) if all_members_role else {}

        role = LibraryRole(
            tenant_id=tenant_id,
            library_id=library_id,
            role_kind=LibraryRoleKind.CUSTOM,
            code=code,
            name=name,
            description=description,
            system_builtin=False,
            permissions=default_permissions,
            status="active",
        )
        session.add(role)
        await session.flush()
        return role

    @staticmethod
    async def _get_all_members_role(
        session: AsyncSession,
        library_id: str,
    ) -> LibraryRole | None:
        """获取全员权限组"""
        tenant_id = get_tenant_id()
        stmt = select(LibraryRole).where(
            LibraryRole.library_id == library_id,
            LibraryRole.tenant_id == tenant_id,
            LibraryRole.role_kind == LibraryRoleKind.ALL_MEMBERS,
            LibraryRole.status == "active",
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    # ==================== 权限组成员 ====================

    @staticmethod
    async def list_role_members(
        session: AsyncSession,
        role_id: str,
    ) -> list[LibraryRoleMember]:
        """查询权限组成员"""
        tenant_id = get_tenant_id()
        stmt = select(LibraryRoleMember).where(
            LibraryRoleMember.role_id == role_id,
            LibraryRoleMember.tenant_id == tenant_id,
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def add_role_member(
        session: AsyncSession,
        library_id: str,
        role_id: str,
        user_id: str,
    ) -> LibraryRoleMember:
        """添加权限组成员"""
        tenant_id = get_tenant_id()
        member = LibraryRoleMember(
            tenant_id=tenant_id,
            library_id=library_id,
            role_id=role_id,
            user_id=user_id,
        )
        session.add(member)
        await session.flush()
        return member

    # ==================== 资源 ACL ====================

    @staticmethod
    async def list_resource_acls(
        session: AsyncSession,
        library_id: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> list[ResourceAcl]:
        """查询资源 ACL 列表"""
        tenant_id = get_tenant_id()
        conditions = [ResourceAcl.library_id == library_id, ResourceAcl.tenant_id == tenant_id, ResourceAcl.status == ResourceAclStatus.ACTIVE]
        if resource_type:
            conditions.append(ResourceAcl.resource_type == resource_type)
        if resource_id:
            conditions.append(ResourceAcl.resource_id == resource_id)

        stmt = select(ResourceAcl).where(*conditions).order_by(ResourceAcl.priority.desc())
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def create_resource_acl(
        session: AsyncSession,
        library_id: str,
        resource_type: str,
        resource_id: str,
        subject_id: str,
        subject_type: str = "user",
        action: str = "read",
        effect: str = ResourceAclEffect.ALLOW,
        priority: int = 0,
    ) -> ResourceAcl:
        """创建资源 ACL"""
        tenant_id = get_tenant_id()

        acl = ResourceAcl(
            tenant_id=tenant_id,
            library_id=library_id,
            resource_type=resource_type,
            resource_id=resource_id,
            subject_id=subject_id,
            subject_type=subject_type,
            action=action,
            effect=effect,
            priority=priority,
            status=ResourceAclStatus.ACTIVE,
        )
        session.add(acl)
        await session.flush()
        return acl

    @staticmethod
    async def update_inheritance(
        session: AsyncSession,
        library_id: str,
        resource_type: str,
        resource_id: str,
        inherit_enabled: bool,
    ) -> None:
        """更新权限继承（关闭继承时截断继承链 ACL）"""
        tenant_id = get_tenant_id()

        if not inherit_enabled:
            # 关闭继承：标记继承来源的 ACL 为 disabled
            stmt = select(ResourceAcl).where(
                ResourceAcl.library_id == library_id,
                ResourceAcl.tenant_id == tenant_id,
                ResourceAcl.resource_id == resource_id,
                ResourceAcl.inherited_from_resource_id.isnot(None),
                ResourceAcl.status == ResourceAclStatus.ACTIVE,
            )
            result = await session.execute(stmt)
            inherited_acls = list(result.scalars().all())
            for acl in inherited_acls:
                acl.status = ResourceAclStatus.DISABLED

        await session.flush()


permission_config_service = PermissionConfigService()
