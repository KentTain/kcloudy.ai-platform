"""
部门管理服务

使用 TreeNodeMixin 内置方法简化树字段维护逻辑。
"""

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Department, User, UserDepartment

_logger = logger.bind(name=__name__)


class DepartmentService:
    """部门管理服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        tenant_id: str,
        name: str,
        parent_id: str | None = None,
        code: str | None = None,
        sort_order: int = 0,
        leader_id: str | None = None,
    ) -> Department:
        """创建部门"""
        source = {
            "tenant_id": tenant_id,
            "name": name,
            "code": code,
            "sort_order": sort_order,
            "leader_id": leader_id,
        }
        if parent_id:
            source["parent_id"] = parent_id

        dept = await Department.create_node(session, source)
        await session.flush()
        await session.refresh(dept)

        _logger.info(f"创建部门: {name}")
        return dept

    @staticmethod
    async def get_by_id(session: AsyncSession, department_id: str) -> Department | None:
        """根据 ID 获取部门"""
        stmt = select(Department).where(Department.id == department_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(session: AsyncSession, department_ids: list[str]) -> list[Department]:
        """批量获取部门"""
        if not department_ids:
            return []
        stmt = select(Department).where(Department.id.in_(department_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        department_id: str,
        name: str | None = None,
        code: str | None = None,
        parent_id: str | None = None,
        sort_order: int | None = None,
        leader_id: str | None = None,
        status: str | None = None,
    ) -> Department:
        """更新部门"""
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

        dept = await Department.update_node(session, department_id, source)
        await session.flush()
        await session.refresh(dept)

        _logger.info(f"更新部门: {department_id}")
        return dept

    @staticmethod
    async def delete(session: AsyncSession, department_id: str) -> bool:
        """删除部门"""
        # 检查是否有用户
        stmt = select(func.count(UserDepartment.id)).where(
            UserDepartment.department_id == department_id
        )
        result = await session.execute(stmt)
        if result.scalar() > 0:
            raise ValueError("部门下存在用户，无法删除")

        count = await Department.delete_node(session, department_id)
        await session.flush()

        if count > 0:
            _logger.info(f"删除部门: {department_id}，影响 {count} 个节点")
            return True
        return False

    @staticmethod
    async def list_by_tenant(session: AsyncSession, tenant_id: str) -> list[Department]:
        """获取租户的所有部门"""
        stmt = (
            select(Department)
            .where(Department.tenant_id == tenant_id)
            .order_by(Department.tree_sorts)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_tree(session: AsyncSession, tenant_id: str) -> list[dict]:
        """
        获取部门树形结构

        使用 TreeNodeMixin 内置方法构建树。
        """
        stmt = (
            select(Department)
            .where(Department.tenant_id == tenant_id)
            .order_by(Department.tree_sorts)
        )
        result = await session.execute(stmt)
        nodes = result.scalars().all()
        return Department.build_tree(nodes)

    @staticmethod
    async def add_user(session: AsyncSession, department_id: str, user_id: str, is_leader: bool = False) -> UserDepartment:
        """
        添加用户到部门

        自动从部门推导 tenant_id 用于关联表。

        Args:
            session: 数据库会话
            department_id: 部门 ID
            user_id: 用户 ID
            is_leader: 是否部门负责人

        Returns:
            UserDepartment
        """
        # 获取部门的 tenant_id
        stmt = select(Department).where(Department.id == department_id)
        result = await session.execute(stmt)
        dept = result.scalar_one_or_none()
        if not dept:
            raise ValueError("部门不存在")

        tenant_id = dept.tenant_id

        stmt = select(UserDepartment).where(
            UserDepartment.department_id == department_id,
            UserDepartment.user_id == user_id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("用户已在该部门中")

        ud = UserDepartment(
            department_id=department_id,
            user_id=user_id,
            is_leader=is_leader,
            tenant_id=tenant_id,
        )
        session.add(ud)
        await session.flush()
        await session.refresh(ud)

        _logger.info(f"添加用户到部门: {user_id} -> {department_id}")
        return ud

    @staticmethod
    async def remove_user(session: AsyncSession, department_id: str, user_id: str) -> bool:
        """从部门移除用户"""
        stmt = select(UserDepartment).where(
            UserDepartment.department_id == department_id,
            UserDepartment.user_id == user_id,
        )
        result = await session.execute(stmt)
        ud = result.scalar_one_or_none()

        if ud:
            await session.delete(ud)
            await session.flush()
            return True
        return False

    @staticmethod
    async def get_department_users(session: AsyncSession, department_id: str) -> list[dict]:
        """获取部门的用户列表"""
        stmt = (
            select(User, UserDepartment.is_leader)
            .join(UserDepartment, User.id == UserDepartment.user_id)
            .where(UserDepartment.department_id == department_id)
            .order_by(UserDepartment.is_leader.desc(), User.username)
        )
        result = await session.execute(stmt)

        users = []
        for row in result:
            user, is_leader = row
            users.append({
                "user_id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "phone": user.phone,
                "is_leader": is_leader,
            })
        return users

    @staticmethod
    async def batch_add_users(department_id: str, user_ids: list[str]) -> int:
        """
        批量添加用户到部门

        Args:
            department_id: 部门 ID
            user_ids: 用户 ID 列表

        Returns:
            成功添加的数量
        """
        async with async_session() as session:
            # 获取部门的 tenant_id
            stmt = select(Department).where(Department.id == department_id)
            result = await session.execute(stmt)
            dept = result.scalar_one_or_none()
            if not dept:
                raise ValueError("部门不存在")

            tenant_id = dept.tenant_id
            added = 0

            for user_id in user_ids:
                # 检查是否已在部门中
                stmt = select(UserDepartment).where(
                    UserDepartment.department_id == department_id,
                    UserDepartment.user_id == user_id,
                )
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    continue  # 跳过已存在的

                ud = UserDepartment(
                    department_id=department_id,
                    user_id=user_id,
                    is_leader=False,
                    tenant_id=tenant_id,
                )
                session.add(ud)
                added += 1

            await session.commit()
            _logger.info(f"批量添加用户到部门: {department_id} -> {added} 人")
            return added

    @staticmethod
    async def get_department_stats(department_id: str) -> dict:
        """
        获取部门统计信息（直属成员数、总成员数、路径等）

        Args:
            department_id: 部门 ID

        Returns:
            dict: 包含 direct_member_count, total_member_count, path, children_count 等
        """
        async with async_session() as session:
            # 获取部门基本信息
            stmt = select(Department).where(Department.id == department_id)
            result = await session.execute(stmt)
            dept = result.scalar_one_or_none()
            if not dept:
                raise ValueError("部门不存在")

            # 直属成员数
            stmt = select(func.count(UserDepartment.id)).where(
                UserDepartment.department_id == department_id
            )
            result = await session.execute(stmt)
            direct_member_count = result.scalar() or 0

            # 下级部门 ID（通过 parent_ids 前缀匹配）
            stmt = select(Department.id).where(
                Department.tenant_id == dept.tenant_id,
                Department.parent_ids.like(f"{dept.parent_ids}{dept.id}/%"),
            )
            result = await session.execute(stmt)
            child_dept_ids = [row[0] for row in result.fetchall()]
            child_dept_ids.append(department_id)

            # 总成员数（含下级部门）
            stmt = select(func.count(UserDepartment.id.distinct())).where(
                UserDepartment.department_id.in_(child_dept_ids)
            )
            result = await session.execute(stmt)
            total_member_count = result.scalar() or 0

            # 直接子组织数
            stmt = select(func.count(Department.id)).where(
                Department.parent_id == department_id,
                Department.tenant_id == dept.tenant_id,
            )
            result = await session.execute(stmt)
            children_count = result.scalar() or 0

            # 组织路径
            path = dept.tree_names if dept.tree_names else dept.name

            return {
                "direct_member_count": direct_member_count,
                "total_member_count": total_member_count,
                "children_count": children_count,
                "path": path,
            }


# 服务单例
department_service = DepartmentService()