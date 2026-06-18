"""
系统设置服务

提供系统设置的 CRUD 业务逻辑。
"""

from typing import Any

from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from iam.models import SystemSetting, SystemSettingAttribute

_logger = logger.bind(name=__name__)


class SystemSettingService:
    """系统设置服务"""

    @staticmethod
    async def create_setting(
        session: AsyncSession,
        tenant_id: str,
        code: str,
        name: str,
        display_name: str | None = None,
        description: str | None = None,
        application_id: str | None = None,
        application_name: str | None = None,
        can_edit: bool = True,
        is_require: bool = False,
        index: int = 0,
        attributes: list[dict[str, Any]] | None = None,
    ) -> SystemSetting:
        """
        创建配置及其属性值

        Args:
            session: 数据库会话
            tenant_id: 租户ID
            code: 设置编号
            name: 名称
            display_name: 显示名称
            description: 描述
            application_id: 应用程序Id
            application_name: 应用程序名称
            can_edit: 是否能编辑
            is_require: 是否必须
            index: 排序
            attributes: 属性值列表

        Returns:
            创建的配置
        """
        setting = SystemSetting(
            tenant_id=tenant_id,
            code=code,
            name=name,
            display_name=display_name,
            description=description,
            application_id=application_id,
            application_name=application_name,
            can_edit=can_edit,
            is_require=is_require,
            index=index,
        )
        session.add(setting)
        await session.flush()

        if attributes:
            for attr_data in attributes:
                attr = SystemSettingAttribute(
                    tenant_id=tenant_id,
                    setting_id=setting.id,
                    name=attr_data.get("name"),
                    display_name=attr_data.get("display_name"),
                    description=attr_data.get("description"),
                    data_type=attr_data.get("data_type", "string"),
                    value=attr_data.get("value"),
                    ext_data=attr_data.get("ext_data"),
                    can_edit=attr_data.get("can_edit", True),
                    is_require=attr_data.get("is_require", False),
                    index=attr_data.get("index", 0),
                )
                session.add(attr)

        await session.flush()
        await session.refresh(setting, ["attributes"])

        _logger.info(f"创建系统设置: {code}")
        return setting

    @staticmethod
    async def get_setting(session: AsyncSession, setting_id: str) -> SystemSetting | None:
        """
        获取配置详情（含属性值）

        Args:
            session: 数据库会话
            setting_id: 配置ID

        Returns:
            配置详情，未找到返回 None
        """
        stmt = (
            select(SystemSetting)
            .options(selectinload(SystemSetting.attributes))
            .where(SystemSetting.id == setting_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_setting_by_code(session: AsyncSession, tenant_id: str, code: str) -> SystemSetting | None:
        """
        按编号获取配置

        Args:
            session: 数据库会话
            tenant_id: 租户ID
            code: 设置编号

        Returns:
            配置详情，未找到返回 None
        """
        stmt = (
            select(SystemSetting)
            .options(selectinload(SystemSetting.attributes))
            .where(SystemSetting.tenant_id == tenant_id)
            .where(SystemSetting.code == code)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_setting(
        session: AsyncSession,
        setting_id: str,
        code: str | None = None,
        name: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        application_id: str | None = None,
        application_name: str | None = None,
        can_edit: bool | None = None,
        is_require: bool | None = None,
        index: int | None = None,
        attributes: list[dict[str, Any]] | None = None,
    ) -> SystemSetting | None:
        """
        更新配置及其属性值

        Args:
            session: 数据库会话
            setting_id: 配置ID
            name: 名称
            display_name: 显示名称
            description: 描述
            application_id: 应用程序Id
            application_name: 应用程序名称
            can_edit: 是否能编辑
            is_require: 是否必须
            index: 排序
            attributes: 属性值列表（完整替换）

        Returns:
            更新后的配置，未找到返回 None
        """
        stmt = (
            select(SystemSetting)
            .options(selectinload(SystemSetting.attributes))
            .where(SystemSetting.id == setting_id)
        )
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            return None

        if code is not None:
            setting.code = code
        if name is not None:
            setting.name = name
        if display_name is not None:
            setting.display_name = display_name
        if description is not None:
            setting.description = description
        if application_id is not None:
            setting.application_id = application_id
        if application_name is not None:
            setting.application_name = application_name
        if can_edit is not None:
            setting.can_edit = can_edit
        if is_require is not None:
            setting.is_require = is_require
        if index is not None:
            setting.index = index

        if attributes is not None:
            existing_attrs = {attr.name: attr for attr in setting.attributes}
            new_attr_names = {attr.get("name") for attr in attributes}

            for attr_name, attr in existing_attrs.items():
                if attr_name not in new_attr_names:
                    await session.delete(attr)

            for attr_data in attributes:
                attr_name = attr_data.get("name")
                if attr_name in existing_attrs:
                    attr = existing_attrs[attr_name]
                    attr.display_name = attr_data.get("display_name")
                    attr.description = attr_data.get("description")
                    attr.data_type = attr_data.get("data_type", "string")
                    attr.value = attr_data.get("value")
                    attr.ext_data = attr_data.get("ext_data")
                    attr.can_edit = attr_data.get("can_edit", True)
                    attr.is_require = attr_data.get("is_require", False)
                    attr.index = attr_data.get("index", 0)
                else:
                    attr = SystemSettingAttribute(
                        tenant_id=setting.tenant_id,
                        setting_id=setting.id,
                        name=attr_name,
                        display_name=attr_data.get("display_name"),
                        description=attr_data.get("description"),
                        data_type=attr_data.get("data_type", "string"),
                        value=attr_data.get("value"),
                        ext_data=attr_data.get("ext_data"),
                        can_edit=attr_data.get("can_edit", True),
                        is_require=attr_data.get("is_require", False),
                        index=attr_data.get("index", 0),
                    )
                    session.add(attr)

        await session.flush()
        await session.refresh(setting, ["attributes"])

        _logger.info(f"更新系统设置: {setting_id}")
        return setting

    @staticmethod
    async def delete_setting(session: AsyncSession, setting_id: str) -> bool:
        """
        删除配置（级联删除属性值）

        Args:
            session: 数据库会话
            setting_id: 配置ID

        Returns:
            是否删除成功
        """
        stmt = select(SystemSetting).where(SystemSetting.id == setting_id)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            return False

        await session.delete(setting)
        await session.flush()

        _logger.info(f"删除系统设置: {setting_id}")
        return True

    @staticmethod
    async def list_settings(
        session: AsyncSession,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
    ) -> tuple[list[SystemSetting], int]:
        """
        列出配置（支持模糊搜索）

        Args:
            session: 数据库会话
            tenant_id: 租户ID
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词

        Returns:
            配置列表和总数
        """
        stmt = (
            select(SystemSetting)
            .options(selectinload(SystemSetting.attributes))
            .where(SystemSetting.tenant_id == tenant_id)
        )

        if keyword:
            stmt = stmt.where(
                or_(
                    SystemSetting.name.contains(keyword),
                    SystemSetting.code.contains(keyword),
                    SystemSetting.display_name.contains(keyword),
                )
            )

        count_stmt = select(func.count()).select_from(SystemSetting).where(SystemSetting.tenant_id == tenant_id)
        if keyword:
            count_stmt = count_stmt.where(
                or_(
                    SystemSetting.name.contains(keyword),
                    SystemSetting.code.contains(keyword),
                    SystemSetting.display_name.contains(keyword),
                )
            )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.order_by(SystemSetting.index).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        settings = list(result.scalars().all())

        return settings, total


system_setting_service = SystemSettingService()
