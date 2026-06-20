"""
模块服务层
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models import Module, TenantModule

_logger = logging.getLogger(__name__)


class ModuleService:
    """模块服务"""

    @staticmethod
    async def list_modules(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Module], int]:
        """
        查询模块列表

        Args:
            session: 数据库会话
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词（名称或编码）
            is_active: 是否启用筛选

        Returns:
            (模块列表, 总数)
        """
        # 构建查询条件
        conditions = []
        if keyword:
            conditions.append(
                (Module.name.ilike(f"%{keyword}%"))
                | (Module.code.ilike(f"%{keyword}%"))
            )
        if is_active is not None:
            conditions.append(Module.is_active == is_active)

        # 查询总数
        count_stmt = select(func.count(Module.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        stmt = select(Module).order_by(Module.created_at.desc())
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        modules = list(result.scalars().all())

        return modules, total

    @staticmethod
    async def get_by_id(session: AsyncSession, module_id: str) -> Module | None:
        """根据 ID 获取模块"""
        stmt = select(Module).where(Module.id == module_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> Module | None:
        """根据编码获取模块"""
        stmt = select(Module).where(Module.code == code)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_active_modules(session: AsyncSession) -> list[Module]:
        """
        获取所有活跃模块列表

        用于构建管理后台的一级模块菜单。

        Args:
            session: 数据库会话

        Returns:
            活跃模块列表
        """
        stmt = (
            select(Module)
            .where(Module.is_active == True)
            .order_by(Module.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        code: str,
        name: str,
        description: str | None = None,
        icon: str | None = None,
        version: str = "1.0.0",
        is_active: bool = True,
        is_need: bool = False,
    ) -> Module:
        """
        创建模块

        Args:
            session: 数据库会话
            code: 模块编码
            name: 模块名称
            description: 模块描述
            icon: 图标标识
            version: 模块版本
            is_active: 是否启用
            is_need: 是否必须模块

        Returns:
            Module
        """
        module = Module(
            code=code,
            name=name,
            description=description,
            icon=icon,
            version=version,
            is_active=is_active,
            is_need=is_need,
        )
        session.add(module)
        # 先 flush 获取 module.id，但不提交事务
        await session.flush()
        await session.refresh(module)

        _logger.info(f"创建模块: {module.id} ({module.code})")
        return module
        _logger.info(f"为模块 {module.code} 创建默认角色: admin, user")

    @staticmethod
    async def update(
        session: AsyncSession,
        module_id: str,
        name: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        version: str | None = None,
        is_active: bool | None = None,
        is_need: bool | None = None,
    ) -> Module | None:
        """
        更新模块

        Args:
            session: 数据库会话
            module_id: 模块 ID
            其他参数为要更新的字段

        Returns:
            Module | None
        """
        stmt = select(Module).where(Module.id == module_id)
        result = await session.execute(stmt)
        module = result.scalar_one_or_none()

        if not module:
            return None

        if name is not None:
            module.name = name
        if description is not None:
            module.description = description
        if icon is not None:
            module.icon = icon
        if version is not None:
            module.version = version
        if is_active is not None:
            module.is_active = is_active
        if is_need is not None:
            module.is_need = is_need

        await session.flush()
        await session.refresh(module)

        return module

    @staticmethod
    async def delete(session: AsyncSession, module_id: str) -> bool:
        """
        删除模块

        检查模块是否被租户分配，若已分配则禁止删除。

        Args:
            session: 数据库会话
            module_id: 模块 ID

        Returns:
            bool: 是否删除成功

        Raises:
            ValueError: 模块已被租户分配，无法删除
        """
        # 检查模块是否存在
        stmt = select(Module).where(Module.id == module_id)
        result = await session.execute(stmt)
        module = result.scalar_one_or_none()

        if not module:
            return False

        # 检查是否被租户分配
        tenant_module_stmt = select(func.count(TenantModule.id)).where(
            TenantModule.module_id == module_id
        )
        tenant_count_result = await session.execute(tenant_module_stmt)
        tenant_count = tenant_count_result.scalar() or 0

        if tenant_count > 0:
            raise ValueError(f"模块 {module.code} 已被 {tenant_count} 个租户分配，无法删除")

        # 删除模块（级联删除菜单、权限、角色）
        await session.delete(module)
        await session.flush()

        _logger.info(f"删除模块: {module_id}")
        return True

    @staticmethod
    async def check_module_assigned(session: AsyncSession, module_id: str) -> bool:
        """检查模块是否已被租户分配"""
        stmt = select(func.count(TenantModule.id)).where(
            TenantModule.module_id == module_id
        )
        result = await session.execute(stmt)
        count = result.scalar() or 0
        return count > 0


# 单例实例
module_service = ModuleService()
