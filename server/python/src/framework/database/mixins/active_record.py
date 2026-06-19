"""
ActiveRecord 混入

提供 ActiveRecord 模式的数据库操作方法。
"""

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Self, TypeVar

from loguru import logger
from sqlalchemy import and_, asc, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.pagination import Pagination

T = TypeVar("T", bound="ActiveRecordMixin")
_logger = logger.bind(name=__name__)


class ActiveRecordMixin:
    """
    ActiveRecord 混入类

    提供 ActiveRecord 风格的数据库操作方法，包括：
    - 实例方法：save, delete, update, refresh
    - 类方法：create, count, first, one, all, paginated 系列
    - 支持软删除（自动检测 deleted_at 字段）
    - 支持复杂查询条件
    """

    __abstract__ = True

    # ==================== 属性 ====================

    @property
    def primary_key(self) -> Any:
        """
        获取主键值

        Raises:
            AttributeError: 模型没有主键

        Returns:
            Any: 主键值
        """
        pk_columns = self.__table__.primary_key
        if not pk_columns:
            raise AttributeError("模型没有主键")
        pk_column = next(iter(pk_columns))
        return getattr(self, pk_column.name)

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
        删除实体（支持软删除）

        如果模型有 deleted_at 字段，则执行软删除；
        否则执行物理删除。

        Args:
            session: 数据库会话
        """
        if self._has_deleted_at_attr():
            # 软删除
            self.deleted_at = datetime.now(UTC).replace(tzinfo=None)
            await session.flush()
            await self._publish_event("deleted", self)
        else:
            # 物理删除
            await session.delete(self)
            await session.flush()

    async def update(
        self: T, session: AsyncSession, source: dict[str, Any] | Any | None = None
    ) -> T:
        """
        更新实体属性

        Args:
            session: 数据库会话
            source: 要更新的属性字典或对象

        Returns:
            更新后的实体
        """
        if source is None:
            source = {}

        if not isinstance(source, dict):
            source_dict = {}
            for column in self.__table__.columns:
                if hasattr(source, column.name):
                    source_dict[column.name] = getattr(source, column.name)
            source = source_dict

        for key, value in source.items():
            if hasattr(self, key):
                setattr(self, key, value)

        await session.flush()
        await self._publish_event("updated", self)
        return self

    async def refresh(self: T, session: AsyncSession) -> T:
        """
        从数据库刷新对象

        Args:
            session: 数据库会话

        Returns:
            刷新后的实体
        """
        await session.refresh(self)
        return self

    # ==================== 类方法 - 转换 ====================

    @classmethod
    def convert_without_saving(
        cls, source: dict | Any, update: dict | None = None
    ) -> Self | None:
        """
        将源数据转换为模型实例（不保存到数据库）

        Args:
            source: 源数据
            update: 额外更新数据

        Returns:
            模型实例或None
        """
        try:
            source_dict = {}
            if isinstance(source, dict):
                source_dict = source.copy()
            else:
                for column in cls.__table__.columns:
                    if hasattr(source, column.name):
                        source_dict[column.name] = getattr(source, column.name)

            # 检查必填字段（排除 id）
            required_columns = [
                col
                for col in cls.__table__.columns
                if not col.nullable and col.default is None and col.name != "id"
            ]
            for col in required_columns:
                if col.name not in source_dict or source_dict[col.name] is None:
                    raise ValueError(f"必填字段 {col.name} 不能为空")

            obj = cls()
            for key, value in source_dict.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            if update:
                for key, value in update.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)

            return obj
        except Exception:
            _logger.exception("转换模型时出错")
            return None

    # ==================== 类方法 - Count ====================

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """
        返回模型中的记录数量

        Args:
            session: 数据库会话

        Returns:
            int: 记录数量
        """
        statement = select(func.count()).select_from(cls)
        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalar() or 0

    @classmethod
    async def count_by_field(cls, session: AsyncSession, field: str, value: Any) -> int:
        """
        根据字段值获取记录数量

        Args:
            session: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            int: 记录数量
        """
        return await cls.count_by_fields(session, {field: value})

    @classmethod
    async def count_by_fields(
        cls, session: AsyncSession, fields: dict[str, Any]
    ) -> int:
        """
        根据多个字段值获取记录数量

        Args:
            session: 数据库会话
            fields: 字段值字典

        Returns:
            int: 记录数量
        """
        statement = select(func.count()).select_from(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalar() or 0

    @classmethod
    async def count_by_conditions(cls, session: AsyncSession, conditions: list) -> int:
        """
        根据复杂查询条件获取记录数量

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表

        Returns:
            int: 记录数量
        """
        statement = select(func.count()).select_from(cls)
        if conditions:
            statement = statement.where(and_(*conditions))

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalar() or 0

    # ==================== 类方法 - First ====================

    @classmethod
    async def first(cls, session: AsyncSession) -> Self | None:
        """
        获取第一条记录

        Args:
            session: 数据库会话

        Returns:
            第一条记录或None
        """
        statement = select(cls)
        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalars().first()

    @classmethod
    async def first_by_field(
        cls, session: AsyncSession, field: str, value: Any
    ) -> Self | None:
        """
        根据字段值获取第一条记录

        Args:
            session: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            第一条记录或None
        """
        return await cls.first_by_fields(session, {field: value})

    @classmethod
    async def first_by_fields(
        cls, session: AsyncSession, fields: dict[str, Any]
    ) -> Self | None:
        """
        根据多个字段值获取第一条记录

        Args:
            session: 数据库会话
            fields: 字段值字典

        Returns:
            第一条记录或None
        """
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalars().first()

    @classmethod
    async def first_by_conditions(
        cls, session: AsyncSession, conditions: list
    ) -> Self | None:
        """
        根据复杂查询条件获取第一条记录

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表

        Returns:
            第一条记录或None
        """
        statement = select(cls)
        if conditions:
            statement = statement.where(and_(*conditions))

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalars().first()

    # ==================== 类方法 - One ====================

    @classmethod
    async def one_by_id(cls, session: AsyncSession, id: Any) -> Self | None:
        """
        根据 ID 获取单条记录

        Args:
            session: 数据库会话
            id: 记录 ID

        Returns:
            模型记录或None
        """
        return await session.get(cls, id)

    @classmethod
    async def one_by_field(
        cls, session: AsyncSession, field: str, value: Any
    ) -> Self | None:
        """
        根据字段值获取单条记录（多条记录会报错）

        Args:
            session: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            模型记录或None
        """
        return await cls.one_by_fields(session, {field: value})

    @classmethod
    async def one_by_fields(
        cls, session: AsyncSession, fields: dict[str, Any]
    ) -> Self | None:
        """
        根据多个字段值获取单条记录（多条记录会报错）

        Args:
            session: 数据库会话
            fields: 字段值字典

        Returns:
            模型记录或None
        """
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @classmethod
    async def one_by_conditions(
        cls, session: AsyncSession, conditions: list
    ) -> Self | None:
        """
        根据复杂查询条件获取单条记录（多条记录会报错）

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表

        Returns:
            模型记录或None
        """
        statement = select(cls)
        if conditions:
            statement = statement.where(and_(*conditions))

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    # ==================== 类方法 - All ====================

    @classmethod
    async def all(
        cls,
        session: AsyncSession,
        order_by: list[tuple[str, str]] | None = None,
    ) -> Sequence[Self]:
        """
        获取所有记录

        Args:
            session: 数据库会话
            order_by: 排序条件，格式为 [(字段名, "asc"|"desc"), ...]

        Returns:
            模型记录列表
        """
        statement = select(cls)

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        if order_by:
            for field, direction in order_by:
                column = getattr(cls, field)
                statement = statement.order_by(
                    asc(column) if direction.lower() == "asc" else desc(column)
                )

        result = await session.execute(statement)
        return result.scalars().all()

    @classmethod
    async def all_by_field(
        cls,
        session: AsyncSession,
        field: str,
        value: Any,
        order_by: list[tuple[str, str]] | None = None,
    ) -> Sequence[Self]:
        """
        根据字段值获取所有记录

        Args:
            session: 数据库会话
            field: 字段名
            value: 字段值
            order_by: 排序条件

        Returns:
            模型记录列表
        """
        return await cls.all_by_fields(session, {field: value}, order_by)

    @classmethod
    async def all_by_fields(
        cls,
        session: AsyncSession,
        fields: dict[str, Any],
        order_by: list[tuple[str, str]] | None = None,
    ) -> Sequence[Self]:
        """
        根据多个字段值获取所有记录

        Args:
            session: 数据库会话
            fields: 字段值字典
            order_by: 排序条件

        Returns:
            模型记录列表
        """
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        if order_by:
            for field, direction in order_by:
                column = getattr(cls, field)
                statement = statement.order_by(
                    asc(column) if direction.lower() == "asc" else desc(column)
                )

        result = await session.execute(statement)
        return result.scalars().all()

    @classmethod
    async def all_by_conditions(
        cls,
        session: AsyncSession,
        conditions: list,
        order_by: list[tuple[str, str]] | None = None,
    ) -> Sequence[Self]:
        """
        根据复杂查询条件获取所有记录

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表
            order_by: 排序条件

        Returns:
            模型记录列表
        """
        statement = select(cls)
        if conditions:
            statement = statement.where(and_(*conditions))

        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        if order_by:
            for field, direction in order_by:
                column = getattr(cls, field)
                statement = statement.order_by(
                    asc(column) if direction.lower() == "asc" else desc(column)
                )

        result = await session.execute(statement)
        return result.scalars().all()

    # ==================== 类方法 - Paginated ====================

    @classmethod
    async def paginated(
        cls,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 100,
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[Sequence[Self], Pagination]:
        """
        简单分页方法

        Args:
            session: 数据库会话
            page: 页码，从1开始
            page_size: 每页记录数
            order_by: 排序条件

        Returns:
            记录列表和分页信息的元组
        """
        return await cls.paginated_by_query(
            session=session, page=page, page_size=page_size, order_by=order_by
        )

    @classmethod
    async def paginated_by_field(
        cls,
        session: AsyncSession,
        field: str,
        value: Any,
        page: int = 1,
        page_size: int = 100,
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[Sequence[Self], Pagination]:
        """
        根据单个字段值进行分页查询

        Args:
            session: 数据库会话
            field: 字段名
            value: 字段值
            page: 页码
            page_size: 每页记录数
            order_by: 排序条件

        Returns:
            记录列表和分页信息的元组
        """
        return await cls.paginated_by_query(
            session=session,
            fields={field: value},
            page=page,
            page_size=page_size,
            order_by=order_by,
        )

    @classmethod
    async def paginated_by_fields(
        cls,
        session: AsyncSession,
        fields: dict[str, Any],
        page: int = 1,
        page_size: int = 100,
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[Sequence[Self], Pagination]:
        """
        根据多个字段值进行分页查询

        Args:
            session: 数据库会话
            fields: 字段值字典
            page: 页码
            page_size: 每页记录数
            order_by: 排序条件

        Returns:
            记录列表和分页信息的元组
        """
        return await cls.paginated_by_query(
            session=session,
            fields=fields,
            page=page,
            page_size=page_size,
            order_by=order_by,
        )

    @classmethod
    async def paginated_by_conditions(
        cls,
        session: AsyncSession,
        conditions: list,
        page: int = 1,
        page_size: int = 100,
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[Sequence[Self], Pagination]:
        """
        根据复杂查询条件进行分页查询

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表
            page: 页码
            page_size: 每页记录数
            order_by: 排序条件

        Returns:
            记录列表和分页信息的元组
        """
        return await cls.paginated_by_query(
            session=session,
            conditions=conditions,
            page=page,
            page_size=page_size,
            order_by=order_by,
        )

    @classmethod
    async def paginated_by_query(
        cls,
        session: AsyncSession,
        fields: dict[str, Any] | None = None,
        conditions: list | None = None,
        page: int = 1,
        page_size: int = 100,
        order_by: list[tuple[str, str]] | None = None,
    ) -> tuple[Sequence[Self], Pagination]:
        """
        通用分页查询方法

        Args:
            session: 数据库会话
            fields: 字段值字典（精确匹配）
            conditions: SQLAlchemy 查询条件列表
            page: 页码
            page_size: 每页记录数
            order_by: 排序条件

        Returns:
            记录列表和分页信息的元组
        """
        # 构建基础查询
        statement = select(cls)

        # 添加字段条件
        if fields:
            for key, value in fields.items():
                statement = statement.where(getattr(cls, key) == value)

        # 添加复杂条件
        if conditions:
            statement = statement.where(and_(*conditions))

        # 软删除过滤
        if cls._has_deleted_at_attr():
            statement = statement.where(cls.deleted_at.is_(None))

        # 获取总数
        count_statement = select(func.count()).select_from(statement.subquery())
        total_result = await session.execute(count_statement)
        total = total_result.scalar() or 0

        # 计算总页数
        total_page = math.ceil(total / page_size) if total > 0 else 1

        # 添加排序
        if order_by:
            for field, direction in order_by:
                column = getattr(cls, field)
                statement = statement.order_by(
                    asc(column) if direction.lower() == "asc" else desc(column)
                )

        # 添加分页
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

        result = await session.execute(statement)
        records = result.scalars().all()

        pagination = Pagination(
            page=page, page_size=page_size, total=total, total_page=total_page
        )

        return records, pagination

    # ==================== 类方法 - Create ====================

    @classmethod
    async def create(cls, session: AsyncSession, source: dict[str, Any]) -> Self:
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
        await cls._publish_event("created", instance)
        return instance

    @classmethod
    async def create_all(
        cls,
        session: AsyncSession,
        sources: list[dict | Any],
        update: dict | None = None,
        batch_size: int = 1000,
    ) -> tuple[list[Self], list[dict | Any]]:
        """
        批量创建记录

        Args:
            session: 数据库会话
            sources: 源数据列表
            update: 额外更新数据
            batch_size: 单次批量创建的最大记录数

        Returns:
            成功创建的记录列表和失败的源数据列表
        """
        if len(sources) > batch_size:
            raise ValueError(
                f"批量创建记录数量({len(sources)})超过最大限制({batch_size})"
            )

        success_records = []
        failed_sources = []

        try:
            objects = []
            for source in sources:
                obj = cls.convert_without_saving(source, update)
                if obj is not None:
                    objects.append(obj)
                else:
                    failed_sources.append(source)

            if objects:
                session.add_all(objects)
                await session.flush()

                for obj in objects:
                    await cls._publish_event("created", obj)
                    success_records.append(obj)

        except Exception:
            _logger.exception("批量创建记录时出错")
            failed_sources.extend([s for s in sources if s not in failed_sources])

        return success_records, failed_sources

    # ==================== 类方法 - Update ====================

    @classmethod
    async def update_by_id(
        cls,
        session: AsyncSession,
        id: Any,
        source: dict | Any,
        update: dict | None = None,
    ) -> Self | None:
        """
        根据 ID 更新记录

        Args:
            session: 数据库会话
            id: 记录 ID
            source: 更新数据源
            update: 额外更新数据

        Returns:
            更新后的记录或None
        """
        try:
            existing = await session.get(cls, id)
            if existing is None:
                return None

            update_data = {}
            if isinstance(source, dict):
                update_data.update(source)
            else:
                for column in cls.__table__.columns:
                    if hasattr(source, column.name):
                        update_data[column.name] = getattr(source, column.name)

            if update:
                update_data.update(update)

            await existing.update(session, update_data)
            return existing

        except Exception as e:
            _logger.exception("根据ID更新记录失败")
            raise e

    @classmethod
    async def update_by_field(
        cls,
        session: AsyncSession,
        field: str,
        value: Any,
        source: dict | Any,
        update: dict | None = None,
    ) -> Self | None:
        """
        根据字段值更新第一条匹配的记录

        Args:
            session: 数据库会话
            field: 查找字段名
            value: 查找字段值
            source: 更新数据源
            update: 额外更新数据

        Returns:
            更新后的记录或None
        """
        return await cls.update_by_fields(
            session, fields={field: value}, source=source, update=update
        )

    @classmethod
    async def update_by_fields(
        cls,
        session: AsyncSession,
        fields: dict[str, Any],
        source: dict | Any,
        update: dict | None = None,
    ) -> Self | None:
        """
        根据多个字段值更新第一条匹配的记录

        Args:
            session: 数据库会话
            fields: 查找条件字段字典
            source: 更新数据源
            update: 额外更新数据

        Returns:
            更新后的记录或None
        """
        try:
            existing = await cls.first_by_fields(session, fields)
            if existing is None:
                return None

            update_data = {}
            if isinstance(source, dict):
                update_data.update(source)
            else:
                for column in cls.__table__.columns:
                    if hasattr(source, column.name):
                        update_data[column.name] = getattr(source, column.name)

            if update:
                update_data.update(update)

            await existing.update(session, update_data)
            return existing

        except Exception as e:
            _logger.exception("根据字段更新记录失败")
            raise e

    @classmethod
    async def update_by_conditions(
        cls,
        session: AsyncSession,
        conditions: list,
        source: dict | Any,
        update: dict | None = None,
    ) -> Self | None:
        """
        根据复杂查询条件更新第一条匹配的记录

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表
            source: 更新数据源
            update: 额外更新数据

        Returns:
            更新后的记录或None
        """
        try:
            existing = await cls.first_by_conditions(session, conditions)
            if existing is None:
                return None

            update_data = {}
            if isinstance(source, dict):
                update_data.update(source)
            else:
                for column in cls.__table__.columns:
                    if hasattr(source, column.name):
                        update_data[column.name] = getattr(source, column.name)

            if update:
                update_data.update(update)

            await existing.update(session, update_data)
            return existing

        except Exception as e:
            _logger.exception("根据条件更新记录失败")
            raise e

    # ==================== 类方法 - Delete ====================

    @classmethod
    async def delete_by_id(cls, session: AsyncSession, id: Any) -> bool:
        """
        根据 ID 删除记录（支持软删除）

        Args:
            session: 数据库会话
            id: 记录 ID

        Returns:
            是否删除成功
        """
        existing = await session.get(cls, id)
        if existing is None:
            return False

        await existing.delete(session)
        return True

    @classmethod
    async def delete_by_field(
        cls, session: AsyncSession, field: str, value: Any
    ) -> bool:
        """
        根据字段值删除第一条匹配的记录

        Args:
            session: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            是否删除成功
        """
        existing = await cls.first_by_field(session, field, value)
        if existing is None:
            return False

        await existing.delete(session)
        return True

    @classmethod
    async def delete_by_fields(
        cls, session: AsyncSession, fields: dict[str, Any]
    ) -> bool:
        """
        根据多个字段值删除第一条匹配的记录

        Args:
            session: 数据库会话
            fields: 字段值字典

        Returns:
            是否删除成功
        """
        existing = await cls.first_by_fields(session, fields)
        if existing is None:
            return False

        await existing.delete(session)
        return True

    @classmethod
    async def delete_by_conditions(cls, session: AsyncSession, conditions: list) -> int:
        """
        根据复杂查询条件删除所有匹配的记录

        Args:
            session: 数据库会话
            conditions: SQLAlchemy 查询条件列表

        Returns:
            删除的记录数量
        """
        if cls._has_deleted_at_attr():
            # 软删除
            now = datetime.now(UTC).replace(tzinfo=None)
            stmt = update(cls).where(and_(*conditions)).values(deleted_at=now)
            result = await session.execute(stmt)
            await session.flush()
            return result.rowcount or 0
        else:
            # 物理删除 - 先查询再逐个删除
            records = await cls.all_by_conditions(session, conditions)
            count = len(records)
            for record in records:
                await session.delete(record)
            await session.flush()
            return count

    # ==================== 内部方法 ====================

    @classmethod
    def _has_deleted_at_attr(cls) -> bool:
        """检查模型是否支持软删除"""
        return hasattr(cls, "deleted_at")

    @classmethod
    async def _publish_event(cls, event_type: str, data: Any) -> None:
        """
        发布事件（供子类覆盖）

        业务模块可定义 _publish_event 方法启用事件发布。

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        publisher = getattr(cls, "_publish_event", None)
        if publisher and publisher != cls._publish_event:
            await publisher(event_type, data)

    # ==================== 兼容方法 ====================

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: str) -> Self | None:
        """根据 ID 获取实体（one_by_id 的别名）"""
        return await cls.one_by_id(session, id)

    @classmethod
    async def get_all(cls, session: AsyncSession) -> list[Self]:
        """获取所有实体（all 的别名）"""
        result = await cls.all(session)
        return list(result)
