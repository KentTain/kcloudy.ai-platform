"""
管理后台插件定义控制器

提供插件定义管理 API：
- 列表查询（分页、筛选）
- 详情查看
- 更新（标记推荐/禁用）
- 删除（检查引用计数）
- 统计数据
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from tenant.schemas.plugin import (
    PluginDefinitionDetailResponse,
    PluginDefinitionPaginatedResponse,
    PluginDefinitionQuery,
    PluginStatisticsResponse,
    UpdatePluginDefinitionRequest,
)
from tenant.services.plugin_definition_service import plugin_definition_service
from tenant.services.plugin_statistics_service import plugin_statistics_service

router = APIRouter()


@router.get("/plugin-definitions")
async def list_plugin_definitions(
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    type: str | None = None,
    is_recommended: bool | None = None,
    is_enabled: bool | None = None,
) -> ApiResponse:
    """
    获取插件定义列表（分页）

    场景：平台管理员查询插件定义列表
    WHEN 管理员请求 GET /tenant/admin/v1/plugin-definitions
    THEN 返回插件定义分页列表，支持关键词搜索、类型筛选、推荐/启用状态筛选
    """
    query = PluginDefinitionQuery(
        page=page,
        page_size=page_size,
        keyword=keyword,
        type=type,
        is_recommended=is_recommended,
        is_enabled=is_enabled,
    )
    result = await plugin_definition_service.list_definitions(session, query)
    return ApiResponse.success(data=result.model_dump())


@router.get("/plugin-definitions/statistics")
async def get_plugin_statistics(
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    获取插件统计数据

    场景：平台管理员查看插件定义统计数据
    WHEN 管理员请求 GET /tenant/admin/v1/plugin-definitions/statistics
    THEN 返回统计数据，包含 definition_stats（总数、按类型分布、推荐数、启用数）
         和 installation_stats（总安装数、活跃安装数、本周新增安装数）
    """
    statistics = await plugin_statistics_service.get_statistics(session)
    return ApiResponse.success(data=statistics.model_dump())


@router.get("/plugin-definitions/{plugin_id}")
async def get_plugin_definition_detail(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    获取插件定义详情

    场景：平台管理员查看插件定义详情
    WHEN 管理员请求 GET /tenant/admin/v1/plugin-definitions/{plugin_id}
    THEN 返回插件定义详情，包含完整的 declaration 内容
    """
    result = await plugin_definition_service.get_definition_detail(session, plugin_id)
    return ApiResponse.success(data=result.model_dump())


@router.patch("/plugin-definitions/{plugin_id}")
async def update_plugin_definition(
    plugin_id: str,
    request: UpdatePluginDefinitionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    更新插件定义（标记推荐/禁用）

    场景：平台管理员标记插件定义为推荐或禁用
    WHEN 管理员请求 PATCH /tenant/admin/v1/plugin-definitions/{plugin_id}
    THEN 更新插件定义的 is_recommended 或 is_enabled 字段
    """
    result = await plugin_definition_service.update_definition(
        session, plugin_id, request
    )
    return ApiResponse.success(data=result.model_dump())


@router.delete("/plugin-definitions/{plugin_id}")
async def delete_plugin_definition(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    删除插件定义

    场景：平台管理员删除插件定义
    WHEN 管理员请求 DELETE /tenant/admin/v1/plugin-definitions/{plugin_id}
    THEN 检查 refers > 0 时禁止删除，否则删除定义

    Raises:
        ConflictError: 插件定义仍被租户引用（refers > 0）
    """
    await plugin_definition_service.delete_definition(session, plugin_id)
    return ApiResponse.success(message="插件定义已删除")
