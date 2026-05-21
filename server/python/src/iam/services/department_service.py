"""
部门管理服务

提供部门 CRUD 和树形结构查询功能。
"""

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

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
            dept = Department(
                tenant_id=tenant_id,
                name=name,
                parent_id=parent_id,
                code=code,
                sort_order=sort_order,
                leader_id=leader_id,
            )
            session.add(dept)
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
    async def update(
        department_id: str,
        name: str | None = None,
        code: str | None = None,
        sort_order: int | None = None,
        leader_id: str | None = None,
        status: str | None = None,
    ) -> Department:
        """更新部门"""
        async with async_session() as session:
            stmt = select(Department).where(Department.id == department_id)
            result = await session.execute(stmt)
            dept = result.scalar_one_or_none()

            if not dept:
                raise ValueError("部门不存在")

            if name is not None:
                dept.name = name
            if code is not None:
                dept.code = code
            if sort_order is not None:
                dept.sort_order = sort_order
            if leader_id is not None:
                dept.leader_id = leader_id
            if status is not None:
                dept.status = status

            await session.commit()
            await session.refresh(dept)

            _logger.info(f"更新部门: {department_id}")
            return dept

    @staticmethod
    async def delete(department_id: str) -> bool:
        """删除部门"""
        async with async_session() as session:
            # 检查是否有子部门
            stmt = select(func.count(Department.id)).where(
                Department.parent_id == department_id
            )
            result = await session.execute(stmt)
            if result.scalar() > 0:
                raise ValueError("存在子部门，无法删除")

            # 检查是否有用户
            stmt = select(func.count(UserDepartment.id)).where(
                UserDepartment.department_id == department_id
            )
            result = await session.execute(stmt)
            if result.scalar() > 0:
                raise ValueError("部门下存在用户，无法删除")

            stmt = select(Department).where(Department.id == department_id)
            result = await session.execute(stmt)
            dept = result.scalar_one_or_none()

            if dept:
                await session.delete(dept)
                await session.commit()
                _logger.info(f"删除部门: {department_id}")
                return True
            return False

    @staticmethod
    async def list_by_tenant(tenant_id: str) -> list[Department]:
        """获取租户的所有部门"""
        async with async_session() as session:
            stmt = (
                select(Department)
                .where(Department.tenant_id == tenant_id)
                .order_by(Department.sort_order, Department.created_at)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_tree(tenant_id: str) -> list[dict]:
        """
        获取部门树形结构

        Args:
            tenant_id: 租户 ID

        Returns:
            list[dict]: 树形结构的部门列表
        """
        departments = await DepartmentService.list_by_tenant(tenant_id)

        # 构建 ID -> 部门映射
        dept_map = {d.id: d for d in departments}

        # 构建树形结构
        tree: list[dict] = []
        for dept in departments:
            node = {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
                "sort_order": dept.sort_order,
                "leader_id": dept.leader_id,
                "status": dept.status,
                "children": [],
            }

            if dept.parent_id and dept.parent_id in dept_map:
                # 添加到父部门的 children
                parent = dept_map[dept.parent_id]
                if not hasattr(parent, "_children"):
                    parent._children = []
                parent._children.append(node)
            else:
                # 顶级部门
                tree.append(node)

        # 将 _children 移到 children
        def move_children(nodes: list[dict]) -> None:
            for node in nodes:
                dept = dept_map.get(node["id"])
                if dept and hasattr(dept, "_children"):
                    node["children"] = dept._children
                    move_children(node["children"])

        move_children(tree)
        return tree

    @staticmethod
    async def add_user(department_id: str, user_id: str, is_leader: bool = False) -> UserDepartment:
        """添加用户到部门"""
        async with async_session() as session:
            # 检查是否已存在
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
