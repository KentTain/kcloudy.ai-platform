"""
组织管理服务

使用 TreeNodeMixin 内置方法简化树字段维护逻辑。
"""

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Organization, User, UserOrganization

_logger = logger.bind(name=__name__)


class OrganizationService:
    """组织管理服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        tenant_id: str,
        name: str,
        parent_id: str | None = None,
        code: str | None = None,
        sort_order: int = 0,
        leader_id: str | None = None,
    ) -> Organization:
        """创建组织"""
        source = {
            "tenant_id": tenant_id,
            "name": name,
            "code": code,
            "sort_order": sort_order,
            "leader_id": leader_id,
        }
        if parent_id:
            source["parent_id"] = parent_id

        org = await Organization.create_node(session, source)
        await session.flush()
        await session.refresh(org)

        _logger.info(f"创建组织: {name}")
        return org

    @staticmethod
    async def get_by_id(session: AsyncSession, organization_id: str) -> Organization | None:
        """根据 ID 获取组织"""
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(
        session: AsyncSession, organization_ids: list[str]
    ) -> list[Organization]:
        """批量获取组织"""
        if not organization_ids:
            return []
        stmt = select(Organization).where(Organization.id.in_(organization_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        organization_id: str,
        name: str | None = None,
        code: str | None = None,
        parent_id: str | None = None,
        sort_order: int | None = None,
        leader_id: str | None = None,
        status: str | None = None,
    ) -> Organization:
        """更新组织"""
        source = {}
        if name is not None:
            source["name"] = name
        if code is not None:
            source["code"] = code
        if parent_id is not None:
            source["parent_id"] = parent_id
        if sort_order is not None:
            source["sort_order"] = sort_order
        if leader_id is not None:
            source["leader_id"] = leader_id
        if status is not None:
            source["status"] = status

        org = await Organization.update_node(session, organization_id, source)
        await session.flush()
        await session.refresh(org)

        _logger.info(f"更新组织: {organization_id}")
        return org

    @staticmethod
    async def delete(session: AsyncSession, organization_id: str) -> bool:
        """删除组织"""
        # 获取组织信息
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await session.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise ValueError("组织不存在")

        # 检查该组织及其子组织是否有关联用户
        stmt = select(func.count(UserOrganization.id)).where(
            UserOrganization.organization_id.in_(
                select(Organization.id).where(
                    Organization.parent_ids.like(f"{org.parent_ids}{org.id},%")
                )
            )
        )
        count = (await session.execute(stmt)).scalar() or 0
        if count > 0:
            raise ValueError("组织或其子组织下存在用户，无法删除")

        count = await Organization.delete_node(session, organization_id)
        await session.flush()

        if count > 0:
            _logger.info(f"删除组织: {organization_id}，影响 {count} 个节点")
            return True
        return False

    @staticmethod
    async def list_by_tenant(session: AsyncSession, tenant_id: str) -> list[Organization]:
        """获取租户的所有组织"""
        stmt = (
            select(Organization)
            .where(Organization.tenant_id == tenant_id)
            .order_by(Organization.tree_sorts)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_tree(session: AsyncSession, tenant_id: str) -> list[dict]:
        """
        获取组织树形结构

        使用 TreeNodeMixin 内置方法构建树，并将 ORM 模型转换为字典。
        """
        from iam.schemas.organization import OrganizationTreeResponse

        stmt = (
            select(Organization)
            .where(Organization.tenant_id == tenant_id)
            .order_by(Organization.tree_sorts)
        )
        result = await session.execute(stmt)
        nodes = result.scalars().all()

        # 使用 transform_func 将 ORM 模型转换为字典
        def transform(org: Organization) -> dict:
            return OrganizationTreeResponse.from_organization(org).model_dump()

        return Organization.build_tree(nodes, transform_func=transform)

    @staticmethod
    async def add_user(
        session: AsyncSession, organization_id: str, user_id: str, is_leader: bool = False
    ) -> UserOrganization:
        """
        添加用户到组织

        自动从组织推导 tenant_id 用于关联表。

        Args:
            session: 数据库会话
            organization_id: 组织 ID
            user_id: 用户 ID
            is_leader: 是否组织负责人

        Returns:
            UserOrganization
        """
        # 获取组织的 tenant_id
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await session.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise ValueError("组织不存在")

        tenant_id = org.tenant_id

        stmt = select(UserOrganization).where(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id == user_id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("用户已在该组织中")

        uo = UserOrganization(
            organization_id=organization_id,
            user_id=user_id,
            is_leader=is_leader,
            tenant_id=tenant_id,
        )
        session.add(uo)
        await session.flush()
        await session.refresh(uo)

        _logger.info(f"添加用户到组织: {user_id} -> {organization_id}")
        return uo

    @staticmethod
    async def remove_user(
        session: AsyncSession, organization_id: str, user_id: str
    ) -> bool:
        """从组织移除用户"""
        stmt = select(UserOrganization).where(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id == user_id,
        )
        result = await session.execute(stmt)
        uo = result.scalar_one_or_none()

        if uo:
            await session.delete(uo)
            await session.flush()
            return True
        return False

    @staticmethod
    async def get_organization_users(
        session: AsyncSession, organization_id: str
    ) -> list[dict]:
        """获取组织的用户列表"""
        stmt = (
            select(User, UserOrganization.is_leader)
            .join(UserOrganization, User.id == UserOrganization.user_id)
            .where(UserOrganization.organization_id == organization_id)
            .order_by(UserOrganization.is_leader.desc(), User.username)
        )
        result = await session.execute(stmt)

        users = []
        for row in result:
            user, is_leader = row
            users.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "email": user.email,
                    "phone": user.phone,
                    "is_leader": is_leader,
                }
            )
        return users

    @staticmethod
    async def batch_add_users(
        session: AsyncSession, organization_id: str, user_ids: list[str]
    ) -> int:
        """
        批量添加用户到组织

        Args:
            organization_id: 组织 ID
            user_ids: 用户 ID 列表

        Returns:
            成功添加的数量
        """
        # 获取组织的 tenant_id
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await session.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise ValueError("组织不存在")

        tenant_id = org.tenant_id
        added = 0

        # 批量查询已存在的关联记录，避免 N+1 查询
        stmt = select(UserOrganization.user_id).where(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id.in_(user_ids),
        )
        result = await session.execute(stmt)
        existing = {row[0] for row in result.fetchall()}

        for user_id in user_ids:
            if user_id in existing:
                continue  # 跳过已存在的

            uo = UserOrganization(
                organization_id=organization_id,
                user_id=user_id,
                is_leader=False,
                tenant_id=tenant_id,
            )
            session.add(uo)
            added += 1

        await session.flush()
        _logger.info(f"批量添加用户到组织: {organization_id} -> {added} 人")
        return added

    @staticmethod
    async def get_organization_stats(session: AsyncSession, organization_id: str) -> dict:
        """
        获取组织统计信息（直属成员数、总成员数、路径等）

        Args:
            organization_id: 组织 ID

        Returns:
            dict: 包含 direct_member_count, total_member_count, path, children_count 等
        """
        # 获取组织基本信息
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await session.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise ValueError("组织不存在")

        # 直属成员数
        stmt = select(func.count(UserOrganization.id)).where(
            UserOrganization.organization_id == organization_id
        )
        result = await session.execute(stmt)
        direct_member_count = result.scalar() or 0

        # 下级组织 ID（通过 parent_ids 前缀匹配）
        stmt = select(Organization.id).where(
            Organization.tenant_id == org.tenant_id,
            Organization.parent_ids.like(f"{org.parent_ids}{org.id},%"),
        )
        result = await session.execute(stmt)
        child_org_ids = [row[0] for row in result.fetchall()]
        child_org_ids.append(organization_id)

        # 总成员数（含下级组织）
        stmt = select(func.count(UserOrganization.id.distinct())).where(
            UserOrganization.organization_id.in_(child_org_ids)
        )
        result = await session.execute(stmt)
        total_member_count = result.scalar() or 0

        # 直接子组织数
        stmt = select(func.count(Organization.id)).where(
            Organization.parent_id == organization_id,
            Organization.tenant_id == org.tenant_id,
        )
        result = await session.execute(stmt)
        children_count = result.scalar() or 0

        # 组织路径
        path = org.tree_names if org.tree_names else org.name

        return {
            "direct_member_count": direct_member_count,
            "total_member_count": total_member_count,
            "children_count": children_count,
            "path": path,
        }


# 服务单例
organization_service = OrganizationService()
