"""
管理后台插件定义控制器

提供插件定义列表查询等 API。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.schemas.plugin import PluginDefinitionResponse

router = APIRouter()


@router.get("/plugins")
async def list_plugin_definitions(
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    获取插件定义列表（按引用数降序）

    场景：查看所有插件定义列表
    WHEN 管理员请求 GET /tenant/admin/v1/plugins
    THEN 返回所有插件定义列表，按引用数降序排列
    """
    result = await session.execute(
        select(TenantPluginDefinition)
        .order_by(desc(TenantPluginDefinition.refers))
    )
    definitions = result.scalars().all()

    items = []
    for d in definitions:
        items.append(PluginDefinitionResponse(
            id=str(d.id),
            plugin_id=d.plugin_id,
            plugin_unique_identifier=d.plugin_unique_identifier,
            refers=d.refers,
            install_type=d.install_type,
            manifest_type=d.manifest_type,
            created_at=d.created_at.isoformat() if d.created_at else None,
            updated_at=d.updated_at.isoformat() if d.updated_at else None,
        ))

    return ApiResponse.success(data=items)
