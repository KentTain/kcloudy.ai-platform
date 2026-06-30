"""
插件市场管理控制器

提供插件市场管理 API：
- 创建市场配置
- 获取市场列表
- 获取市场详情
- 更新市场配置
- 删除市场配置
- 测试市场连接
- 浏览远程插件
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from tenant.middlewares.admin_auth_middleware import require_admin_permission
from tenant.schemas.admin.marketplace import (
    MarketplaceCreate,
    MarketplaceResponse,
    MarketplaceTestResponse,
    MarketplaceUpdate,
    RemotePluginResponse,
)
from tenant.services.marketplace import marketplace_gateway

router = APIRouter()


@router.post("/marketplaces")
async def create_marketplace(
    request: MarketplaceCreate,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    创建市场配置

    场景：平台管理员创建新的插件市场配置
    WHEN 管理员请求 POST /tenant/admin/v1/marketplaces
    THEN 创建市场配置并返回详情
    """
    try:
        marketplace = await marketplace_gateway.create_marketplace(
            session=session,
            name=request.name,
            code=request.code,
            type=request.type,
            url=request.url,
            auth_type=request.auth_type,
            auth_config=request.auth_config,
            description=request.description,
        )
        await session.commit()
        return ApiResponse.success(data=MarketplaceResponse.from_entity(marketplace).model_dump())
    except ValueError as e:
        return ApiResponse.fail(message=str(e))


@router.get("/marketplaces")
async def list_marketplaces(
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
    type: str | None = None,
    is_enabled: bool | None = None,
) -> ApiResponse:
    """
    获取市场列表

    场景：平台管理员查询插件市场列表
    WHEN 管理员请求 GET /tenant/admin/v1/marketplaces
    THEN 返回市场配置列表
    """
    marketplaces = await marketplace_gateway.list_marketplaces(
        session=session,
        is_enabled=is_enabled,
    )
    items = [MarketplaceResponse.from_entity(m).model_dump() for m in marketplaces]
    return ApiResponse.success(data=items)


@router.get("/marketplaces/{marketplace_id}")
async def get_marketplace(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    获取市场详情

    场景：平台管理员查看市场配置详情
    WHEN 管理员请求 GET /tenant/admin/v1/marketplaces/{marketplace_id}
    THEN 返回市场配置详情
    """
    marketplace = await marketplace_gateway.get_marketplace(session, marketplace_id)
    if not marketplace:
        return ApiResponse.fail(message="市场不存在")
    return ApiResponse.success(data=MarketplaceResponse.from_entity(marketplace).model_dump())


@router.put("/marketplaces/{marketplace_id}")
async def update_marketplace(
    marketplace_id: str,
    request: MarketplaceUpdate,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    更新市场配置

    场景：平台管理员更新市场配置
    WHEN 管理员请求 PUT /tenant/admin/v1/marketplaces/{marketplace_id}
    THEN 更新市场配置并返回详情
    """
    try:
        marketplace = await marketplace_gateway.update_marketplace(
            session=session,
            marketplace_id=marketplace_id,
            **request.model_dump(exclude_unset=True),
        )
        await session.commit()
        return ApiResponse.success(data=MarketplaceResponse.from_entity(marketplace).model_dump())
    except ValueError as e:
        return ApiResponse.fail(message=str(e))


@router.delete("/marketplaces/{marketplace_id}")
async def delete_marketplace(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    删除市场配置

    场景：平台管理员删除市场配置
    WHEN 管理员请求 DELETE /tenant/admin/v1/marketplaces/{marketplace_id}
    THEN 删除市场配置
    """
    try:
        await marketplace_gateway.delete_marketplace(session, marketplace_id)
        await session.commit()
        return ApiResponse.success(message="市场已删除")
    except ValueError as e:
        return ApiResponse.fail(message=str(e))


@router.post("/marketplaces/{marketplace_id}/test")
async def test_marketplace(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    测试市场连接

    场景：平台管理员测试市场连接
    WHEN 管理员请求 POST /tenant/admin/v1/marketplaces/{marketplace_id}/test
    THEN 返回连接测试结果
    """
    try:
        result = await marketplace_gateway.test_connection(session, marketplace_id)
        return ApiResponse.success(
            data=MarketplaceTestResponse(
                success=result.success,
                message=result.message,
                plugin_count=result.plugin_count,
                latency_ms=result.latency_ms,
            ).model_dump()
        )
    except ValueError as e:
        return ApiResponse.fail(message=str(e))


@router.get("/marketplaces/{marketplace_id}/plugins")
async def list_remote_plugins(
    marketplace_id: str,
    _perm: None = Depends(require_admin_permission("tenant:marketplace:read")),
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    type: str | None = None,
) -> ApiResponse:
    """
    浏览远程插件

    场景：平台管理员浏览远程市场的插件列表
    WHEN 管理员请求 GET /tenant/admin/v1/marketplaces/{marketplace_id}/plugins
    THEN 返回远程插件分页列表
    """
    try:
        plugins, total = await marketplace_gateway.list_remote_plugins(
            session=session,
            marketplace_id=marketplace_id,
            keyword=keyword,
            plugin_type=type,
            page=page,
            page_size=page_size,
        )
        items = [RemotePluginResponse.from_info(p).model_dump() for p in plugins]
        return ApiResponse.paginated(data=items, total=total, page=page, page_size=page_size)
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
