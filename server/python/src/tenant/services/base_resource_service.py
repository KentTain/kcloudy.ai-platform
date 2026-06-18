"""
资源配置服务基类

提供统一的 CRUD 操作模板和连通性测试抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from loguru import logger
from sqlalchemy import func, select, delete as sql_delete, update as sql_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.exceptions import ConflictError
from framework.database.core.engine import async_session
from framework.utils.resource_crypto import encrypt_password, mask_password

ModelT = TypeVar("ModelT")

_logger = logger.bind(name=__name__)


class BaseResourceService(ABC):
    """资源配置服务基类"""

    # 子类需要覆盖的属性
    model_class: type
    encrypt_fields: list[str] = ["password"]  # 需要加密的字段名列表
    sensitive_fields: list[str] = ["password"]  # 需要脱敏返回的字段列表
    # 子类需要覆盖：配置类对应的 Tenant FK 字段名
    _reference_field: str | None = None

    @classmethod
    async def list_configs(
        cls,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
    ) -> tuple[list[Any], int]:
        """
        获取配置列表（分页）

        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词（匹配 name 字段）

        Returns:
            tuple[list, int]: 配置列表和总数
        """
        async with async_session() as session:
            conditions = []
            if keyword:
                conditions.append(cls.model_class.name.ilike(f"%{keyword}%"))

            # 查询总数
            count_stmt = select(func.count(cls.model_class.id))
            if conditions:
                count_stmt = count_stmt.where(*conditions)
            total_result = await session.execute(count_stmt)
            total = total_result.scalar() or 0

            # 查询列表
            offset = (page - 1) * page_size
            stmt = select(cls.model_class)
            if conditions:
                stmt = stmt.where(*conditions)
            stmt = stmt.order_by(cls.model_class.is_default.desc(), cls.model_class.created_at.desc()).offset(offset).limit(page_size)

            result = await session.execute(stmt)
            items = list(result.scalars().all())

            return items, total

    @classmethod
    async def get_by_id(cls, config_id: str) -> Any | None:
        """
        根据 ID 获取配置

        Args:
            config_id: 配置 ID

        Returns:
            配置模型实例或 None
        """
        async with async_session() as session:
            stmt = select(cls.model_class).where(cls.model_class.id == config_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def _clear_existing_default(cls, s: AsyncSession) -> None:
        """
        清除同类型配置中已有的默认标记

        将同一模型类中所有 is_default=True 的记录设为 False，
        保证全局只有一个默认配置。

        Args:
            s: 数据库会话
        """
        stmt = (
            sql_update(cls.model_class)
            .where(cls.model_class.is_default == True)  # noqa: E712
            .values(is_default=False)
        )
        await s.execute(stmt)
        _logger.debug(f"清除 {cls.model_class.__name__} 已有默认配置标记")

    @classmethod
    async def create(cls, session: AsyncSession | None = None, **kwargs: Any) -> Any:
        """
        创建配置

        当 is_default=True 时，自动清除同类型其他配置的默认标记，
        保证全局唯一性。使用事务保证原子性，捕获 IntegrityError
        处理并发冲突。

        Args:
            session: 数据库会话（可选，用于事务）
            **kwargs: 配置字段

        Returns:
            创建的配置模型实例

        Raises:
            IntegrityError: 并发冲突时重新抛出
        """
        # 加密敏感字段
        for field in cls.encrypt_fields:
            if field in kwargs and kwargs[field] is not None:
                plain = kwargs[field]
                if plain:  # 非空才加密
                    kwargs[field] = encrypt_password(plain)

        is_default = kwargs.get("is_default", False)

        async def _create(s: AsyncSession) -> Any:
            # 如果设置为默认配置，先清除其他默认标记
            if is_default:
                await cls._clear_existing_default(s)

            config = cls.model_class(**kwargs)
            s.add(config)
            await s.commit()
            await s.refresh(config)
            _logger.info(f"创建 {cls.model_class.__name__} 配置: {config.id}" + (" (默认)" if is_default else ""))
            return config

        if session:
            # 如果设置为默认配置，先清除其他默认标记
            if is_default:
                await cls._clear_existing_default(session)

            config = cls.model_class(**kwargs)
            session.add(config)
            await session.flush()
            _logger.info(f"创建 {cls.model_class.__name__} 配置: {config.id}" + (" (默认)" if is_default else ""))
            return config
        else:
            try:
                async with async_session() as s:
                    return await _create(s)
            except IntegrityError:
                _logger.warning(f"创建 {cls.model_class.__name__} 默认配置时发生并发冲突")
                raise

    @classmethod
    async def update(
        cls,
        config_id: str,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> Any | None:
        """
        更新配置

        当更新 is_default 为 True 时，自动清除同类型其他配置的默认标记，
        保证全局唯一性。使用事务保证原子性，捕获 IntegrityError
        处理并发冲突。

        Args:
            config_id: 配置 ID
            session: 数据库会话（可选）
            **kwargs: 要更新的字段

        Returns:
            更新后的配置或 None

        Raises:
            IntegrityError: 并发冲突时重新抛出
        """
        # 加密敏感字段
        for field in cls.encrypt_fields:
            if field in kwargs and kwargs[field] is not None:
                plain = kwargs[field]
                if plain:
                    kwargs[field] = encrypt_password(plain)

        is_setting_default = kwargs.get("is_default", False)

        async def _update(s: AsyncSession) -> Any | None:
            stmt = select(cls.model_class).where(cls.model_class.id == config_id)
            result = await s.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                return None

            # 如果设置为默认配置，先清除其他默认标记
            if is_setting_default:
                await cls._clear_existing_default(s)

            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            await s.commit()
            await s.refresh(config)
            _logger.info(f"更新 {cls.model_class.__name__} 配置: {config_id}" + (" (设为默认)" if is_setting_default else ""))
            return config

        if session:
            stmt = select(cls.model_class).where(cls.model_class.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            if not config:
                return None

            # 如果设置为默认配置，先清除其他默认标记
            if is_setting_default:
                await cls._clear_existing_default(session)

            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            await session.flush()
            _logger.info(f"更新 {cls.model_class.__name__} 配置: {config_id}" + (" (设为默认)" if is_setting_default else ""))
            return config
        else:
            try:
                async with async_session() as s:
                    return await _update(s)
            except IntegrityError:
                _logger.warning(f"更新 {cls.model_class.__name__} 默认配置时发生并发冲突: {config_id}")
                raise

    @classmethod
    async def delete(cls, config_id: str) -> bool:
        """
        删除配置

        如果配置是默认配置或已被租户引用，抛出 ConflictError 异常。

        Args:
            config_id: 配置 ID

        Returns:
            bool: 是否删除成功

        Raises:
            ConflictError: 配置是默认配置或已被租户引用
        """
        async with async_session() as session:
            # 先查询配置是否存在及其状态
            stmt = select(cls.model_class).where(cls.model_class.id == config_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                return False

            # 检查是否为默认配置
            if config.is_default:
                _logger.warning(
                    f"删除 {cls.model_class.__name__} 配置失败: {config_id} 是默认配置"
                )
                raise ConflictError(
                    "此配置是默认配置，删除后新租户将无法自动关联配置"
                )

            # 引用检查
            if cls._reference_field:
                from tenant.models import Tenant

                ref_field = getattr(Tenant, cls._reference_field)
                stmt = select(func.count(Tenant.id)).where(ref_field == config_id)
                result = await session.execute(stmt)
                ref_count = result.scalar() or 0

                if ref_count > 0:
                    _logger.warning(
                        f"删除 {cls.model_class.__name__} 配置失败: {config_id} 被 {ref_count} 个租户引用"
                    )
                    raise ConflictError(
                        f"此配置被租户使用，无法删除"
                    )

            # 执行删除
            stmt = sql_delete(cls.model_class).where(cls.model_class.id == config_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount > 0:
                _logger.info(f"删除 {cls.model_class.__name__} 配置: {config_id}")
                return True
            return False

    @classmethod
    def build_response(cls, config: Any) -> dict[str, Any]:
        """
        构建脱敏后的响应字典

        Args:
            config: 配置模型实例

        Returns:
            dict: 脱敏后的字典
        """
        result = {}
        for column in config.__table__.columns:
            key = column.name
            value = getattr(config, key, None)
            if key in cls.sensitive_fields and value:
                result[key] = mask_password(value)
            else:
                result[key] = value
        return result

    @classmethod
    async def get_default_config(cls, session: AsyncSession | None = None) -> Any | None:
        """
        获取当前类型的默认配置

        查询 is_default=True 的配置记录，返回第一个匹配项。

        Args:
            session: 数据库会话（可选，用于事务中复用）

        Returns:
            默认配置模型实例或 None
        """
        async def _query(s: AsyncSession) -> Any | None:
            stmt = select(cls.model_class).where(cls.model_class.is_default == True).limit(1)  # noqa: E712
            result = await s.execute(stmt)
            return result.scalar_one_or_none()

        if session:
            return await _query(session)
        else:
            async with async_session() as s:
                return await _query(s)

    @classmethod
    @abstractmethod
    async def test_connection(cls, config_id: str) -> tuple[bool, str, int | None]:
        """
        测试连通性

        Args:
            config_id: 配置 ID

        Returns:
            tuple[bool, str, int | None]: 成功/失败、消息、延迟（毫秒）
        """
        ...
