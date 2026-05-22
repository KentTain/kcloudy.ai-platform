"""
ActiveRecord 混入

提供 ActiveRecord 模式的数据库操作方法。
"""

from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound="ActiveRecordMixin")


class ActiveRecordMixin:
    """
    ActiveRecord 混入类

    提供 ActiveRecord 风格的数据库操作方法，包括：
    - 实例方法：save, delete, update
    - 类方法：create, get_by_id, one_by_id, get_all, all
    """

    __abstract__ = True

    # ==================== 实例方法 ====================

    async def save(self: T, session: AsyncSession) -> T:
        """
        保存实体到数据库

        Args:
            session: 数据库会话

        Returns:
            保存后的实体
        """
        session.add(self)
        await session.flush()
        return self

    async def delete(self: T, session: AsyncSession) -> None:
        """
        删除实体

        Args:
            session: 数据库会话
        """
        await session.delete(self)

    async def update(
        self: T, session: AsyncSession, source: dict[str, Any]
    ) -> T:
        """
        更新实体属性

        Args:
            session: 数据库会话
            source: 要更新的属性字典

        Returns:
            更新后的实体
        """
        for key, value in source.items():
            if hasattr(self, key):
                setattr(self, key, value)
        await session.flush()
        return self

    # ==================== 类方法 ====================

    @classmethod
    async def create(
        cls: type[T], session: AsyncSession, source: dict[str, Any]
    ) -> T:
        """
        创建并保存新记录

        Args:
            session: 数据库会话
            source: 实体属性字典

        Returns:
            创建的实体
        """
        instance = cls(**source)
        session.add(instance)
        await session.flush()
        return instance

    @classmethod
    async def get_by_id(cls: type[T], session: AsyncSession, id: str) -> T | None:
        """
        根据 ID 获取实体

        Args:
            session: 数据库会话
            id: 实体 ID

        Returns:
            实体或 None
        """
        result = await session.execute(select(cls).where(cls.id == id))
        return result.scalar_one_or_none()

    @classmethod
    async def one_by_id(cls: type[T], session: AsyncSession, id: str) -> T | None:
        """
        根据 ID 获取实体（get_by_id 的别名）

        Args:
            session: 数据库会话
            id: 实体 ID

        Returns:
            实体或 None
        """
        return await cls.get_by_id(session, id)

    @classmethod
    async def get_all(cls: type[T], session: AsyncSession) -> list[T]:
        """
        获取所有实体

        Args:
            session: 数据库会话

        Returns:
            实体列表
        """
        result = await session.execute(select(cls))
        return list(result.scalars().all())

    @classmethod
    async def all(cls: type[T], session: AsyncSession) -> list[T]:
        """
        获取所有实体（get_all 的别名）

        Args:
            session: 数据库会话

        Returns:
            实体列表
        """
        return await cls.get_all(session)
