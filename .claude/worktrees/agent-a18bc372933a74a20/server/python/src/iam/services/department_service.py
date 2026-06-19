"""
部门管理服务

使用 TreeNodeMixin 内置方法简化树字段维护逻辑。
"""

from loguru import logger
from sqlalchemy import func, select

from iam.models import Department, User, UserDepartment
from framework.database.core.engine import async_session

_logger = logger.bind(name=__name__)


class DepartmentService:
    """部门管理服务"""

    @staticmethod
    async def create(
        tenant_id: str,
        name: str,
        parent_id: str | None = None,
        code: str | None = None,
        sort_order: int = 0,
        leader_id: str | None = None,
    ) -> Department:
        """创建部门"""
        async with async_session() as session:
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
            await session.commit()
            await session.refresh(dept)

            _logger.info(f"创建部门: {name}")
            return dept

    @staticmethod
    async def get_by_id(department_id: str) -> Department | None:
        """根据 ID 获取部门"""
        async with async_session() as session:
            stmt = select(Department).where(Department.id == department_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(department_ids: list[str]) -> list[Department]:
        """批量获取部门"""
        if not department_ids:
            return []
        async with async_session() as session:
            stmt = select(Department).where(Department.id.in_(department_ids))
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def update(
        department_id: str,
        name: str | None = None,
        code: str | None = None,
        parent_id: str | None = None,
        sort_order: int | None = None,
        leader_id: str | None = None,
        status: str | None = None,
    ) -> Department:
        """更新部门"""
        async with async_session() as session:
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
            await session.commit()
            await session.refresh(dept)

            _logger.info(f"更新部门: {department_id}")
            return dept

    @staticmethod
    async def delete(department_id: str) -> bool:
        """删除部门"""
        async with async_session() as session:
            # 检查是否有用户
            stmt = select(func.count(UserDepartment.id)).where(
                UserDepartment.department_id == department_id
            )
            result = await session.execute(stmt)
            if result.scalar() > 0:
                raise ValueError("部门下存在用户，无法删除")

            count = await Department.delete_node(session, department_id)
            await session.commit()

            if count > 0:
                _logger.info(f"删除部门: {department_id}，影响 {count} 个节点")
                return True
            return False

    @staticmethod
    async def list_by_tenant(tenant_id: str) -> list[Department]:
        """获取租户的所有部门"""
        async with async_session() as session:
            stmt = (
                select(Department)
                .where(Department.tenant_id == tenant_id)
                .order_by(Department.tree_sorts)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_tree(tenant_id: str) -> list[dict]:
        """
        获取部门树形结构

        使用 TreeNodeMixin 内置方法构建树。
        """
        async with async_session() as session:
            stmt = (
                select(Department)
                .where(Department.tenant_id == tenant_id)
                .order_by(Department.tree_sorts)
            )
            result = await session.execute(stmt)
            nodes = result.scalars().all()
            return Department.build_tree(nodes)

    @staticmethod
    async def add_user(department_id: str, user_id: str, is_leader: bool = False) -> UserDepartment:
        """
        添加用户到部门

        自动从部门推导 tenant_id 用于关联表。

        Args:
            department_id: 部门 ID
            user_id: 用户 ID
            is_leader: 是否部门负责人

        Returns:
            UserDepartment
        """
        async with async_session() as session:
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
            await session.commit()
            await session.refresh(ud)

            _logger.info(f"添加用户到部门: {user_id} -> {department_id}")
            return ud

    @staticmethod
    async def remove_user(department_id: str, user_id: str) -> bool:
        """从部门移除用户"""
        async with async_session() as session:
            stmt = select(UserDepartment).where(
                UserDepartment.department_id == department_id,
                UserDepartment.user_id == user_id,
            )
            result = await session.execute(stmt)
            ud = result.scalar_one_or_none()

            if ud:
                await session.delete(ud)
                await session.commit()
                return True
            return False

    @staticmethod
    async def get_department_users(department_id: str) -> list[dict]:
        """获取部门的用户列表"""
        async with async_session() as session:
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


# 服务单例
department_service = DepartmentService()