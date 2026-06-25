"""
插件定义服务

提供插件定义的管理功能：查询、更新、删除。
"""

from typing import Any

from loguru import logger
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.exceptions import ConflictError, NotFoundError
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.schemas.plugin import (
    PluginDefinitionDetailResponse,
    PluginDefinitionPaginatedResponse,
    PluginDefinitionQuery,
    PluginDefinitionResponse,
    UpdatePluginDefinitionRequest,
)

_logger = logger.bind(name=__name__)


class PluginDefinitionService:
    """插件定义服务"""

    @staticmethod
    async def list_definitions(
        session: AsyncSession,
        query: PluginDefinitionQuery,
    ) -> PluginDefinitionPaginatedResponse:
        """
        分页查询插件定义列表

        Args:
            session: 数据库会话
            query: 查询参数

        Returns:
            PluginDefinitionPaginatedResponse: 分页响应
        """
        conditions = []

        # 关键词搜索（匹配 plugin_id）
        if query.keyword:
            conditions.append(
                TenantPluginDefinition.plugin_id.ilike(f"%{query.keyword}%")
            )

        # 安装类型筛选
        if query.type:
            conditions.append(TenantPluginDefinition.install_type == query.type)

        # 推荐状态筛选
        if query.is_recommended is not None:
            conditions.append(TenantPluginDefinition.is_recommended == query.is_recommended)

        # 启用状态筛选
        if query.is_enabled is not None:
            conditions.append(TenantPluginDefinition.is_enabled == query.is_enabled)

        # 查询总数
        count_stmt = select(func.count(TenantPluginDefinition.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (query.page - 1) * query.page_size
        stmt = select(TenantPluginDefinition)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = (
            stmt.order_by(TenantPluginDefinition.refers.desc())
            .offset(offset)
            .limit(query.page_size)
        )

        result = await session.execute(stmt)
        definitions = list(result.scalars().all())

        # 转换为响应对象
        items = [PluginDefinitionService._to_response(d) for d in definitions]

        return PluginDefinitionPaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    @staticmethod
    async def get_definition_detail(
        session: AsyncSession,
        plugin_id: str,
    ) -> PluginDefinitionDetailResponse:
        """
        获取插件定义详情

        Args:
            session: 数据库会话
            plugin_id: 插件ID

        Returns:
            PluginDefinitionDetailResponse: 详情响应

        Raises:
            NotFoundError: 插件定义不存在
        """
        stmt = select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_id
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        return PluginDefinitionDetailResponse(
            id=str(definition.id),
            plugin_id=definition.plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            declaration=definition.declaration or {},
            refers=definition.refers,
            install_type=definition.install_type,
            manifest_type=definition.manifest_type,
            is_recommended=definition.is_recommended,
            is_enabled=definition.is_enabled,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )

    @staticmethod
    async def update_definition(
        session: AsyncSession,
        plugin_id: str,
        request: UpdatePluginDefinitionRequest,
    ) -> PluginDefinitionResponse:
        """
        更新插件定义（标记推荐/禁用）

        Args:
            session: 数据库会话
            plugin_id: 插件ID
            request: 更新请求

        Returns:
            PluginDefinitionResponse: 更新后的响应

        Raises:
            NotFoundError: 插件定义不存在
        """
        # 查询现有定义
        stmt = select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_id
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        # 更新字段
        update_data: dict[str, Any] = {}
        if request.is_recommended is not None:
            update_data["is_recommended"] = request.is_recommended
        if request.is_enabled is not None:
            update_data["is_enabled"] = request.is_enabled

        if update_data:
            update_stmt = (
                update(TenantPluginDefinition)
                .where(TenantPluginDefinition.id == definition.id)
                .values(**update_data)
            )
            await session.execute(update_stmt)
            await session.refresh(definition)

        return PluginDefinitionService._to_response(definition)

    @staticmethod
    async def delete_definition(
        session: AsyncSession,
        plugin_id: str,
    ) -> None:
        """
        删除插件定义

        Args:
            session: 数据库会话
            plugin_id: 插件ID

        Raises:
            NotFoundError: 插件定义不存在
            ConflictError: 插件定义仍被租户引用
        """
        # 查询现有定义
        stmt = select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_id
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        # 检查引用计数
        if definition.refers > 0:
            raise ConflictError(
                message=f"无法删除，有 {definition.refers} 个租户正在使用此插件"
            )

        # 删除定义
        delete_stmt = delete(TenantPluginDefinition).where(
            TenantPluginDefinition.id == definition.id
        )
        await session.execute(delete_stmt)

        _logger.info(f"已删除插件定义: {plugin_id}")

    @staticmethod
    def _to_response(definition: TenantPluginDefinition) -> PluginDefinitionResponse:
        """转换模型为响应对象"""
        return PluginDefinitionResponse(
            id=str(definition.id),
            plugin_id=definition.plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            refers=definition.refers,
            install_type=definition.install_type,
            manifest_type=definition.manifest_type,
            is_recommended=definition.is_recommended,
            is_enabled=definition.is_enabled,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )


# 单例实例
plugin_definition_service = PluginDefinitionService()
