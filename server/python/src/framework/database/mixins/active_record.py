"""
ActiveRecord 混入

提供 ActiveRecord 模式的混入类。
"""

from typing import Any, TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound="ActiveRecordMixin")


class ActiveRecordMixin:
    """
    ActiveRecord 混入类

    提供类似 ActiveRecord 的数据库操作方法。
    """

    __abstract__ = True

    async def save(self: T, session: AsyncSession) -> T:
        """
        保存实体

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

    @classmethod
    async def get_by_id(cls: Type[T], session: AsyncSession, id: str) -> T | None:
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
    async def get_all(cls: Type[T], session: AsyncSession) -> list[T]:
        """
        获取所有实体

        Args:
            session: 数据库会话

        Returns:
            实体列表
        """
        result = await session.execute(select(cls))
        return list(result.scalars().all())
