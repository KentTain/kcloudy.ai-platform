"""
租户模块分配控制器
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from tenant.middlewares.admin_auth_middleware import get_current_admin
from tenant.models import Module, TenantModule
from tenant.schemas.admin.tenant_module import (
    AssignModuleRequest,
    TenantModuleResponse,
)
from tenant.services.tenant_module_service import TenantModuleService

router = APIRouter()




async def build_tenant_module_vo(
    session: AsyncSession, tenant_module: TenantModule
) -> TenantModuleResponse:
    """构建租户模块响应对象"""
    stmt = select(Module).where(Module.id == tenant_module.module_id)
    result = await session.execute(stmt)
    module = result.scalar_one_or_none()

    if not module:
        raise ValueError(f"模块不存在: {tenant_module.module_id}")

    return TenantModuleResponse(
        id=tenant_module.id,
        tenant_id=tenant_module.tenant_id,
        module_id=tenant_module.module_id,
        module_code=module.code,
        module_name=module.name,
        module_is_need=module.is_need,
        started_at=tenant_module.started_at,
        expired_at=tenant_module.expired_at,
        is_active=tenant_module.is_active,
        created_at=tenant_module.created_at,
        updated_at=tenant_module.updated_at,
    )


@router.get("/tenants/{tenant_id}/modules")
async def list_tenant_modules(
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取租户已分配的模块列表

    场景：查询租户模块列表
    WHEN 管理员请求 GET /tenant/admin/v1/tenants/{id}/modules
    THEN 返回该租户已分配的所有模块列表
    """
    tenant_modules, total = await TenantModuleService.list_tenant_modules(
        session,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
    )

    items = []
    for tm in tenant_modules:
        vo = await build_tenant_module_vo(session, tm)
        items.append(vo)

    return ApiResponse.paginated(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/tenants/{tenant_id}/modules")
async def assign_module(
    tenant_id: str,
    data: AssignModuleRequest,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    为租户分配模块

    场景：分配模块
    WHEN 管理员请求 POST /tenant/admin/v1/tenants/{id}/modules 并提供模块 ID
    THEN 为租户分配该模块并返回分配记录

    场景：分配已启用的模块
    GIVEN 模块存在且 is_active=true
    WHEN 管理员请求分配
    THEN 创建 TenantModule 记录

    场景：分配未启用的模块
    GIVEN 模块 is_active=false
    WHEN 管理员请求分配
    THEN 返回 HTTP 400 错误

    场景：重复分配模块
    GIVEN 租户已分配该模块
    WHEN 管理员再次请求分配
    THEN 返回 HTTP 400 错误

    场景：为必须模块设置过期时间
    GIVEN 模块 is_need=true
    WHEN 管理员尝试设置过期时间
    THEN 返回 HTTP 400 错误
    """
    try:
        tenant_module = await TenantModuleService.assign_module(
            session,
            tenant_id=tenant_id,
            module_id=data.module_id,
            started_at=data.started_at,
            expired_at=data.expired_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    vo = await build_tenant_module_vo(session, tenant_module)
    return ApiResponse.success(data=vo.model_dump())


@router.delete("/tenants/{tenant_id}/modules/{module_id}")
async def unassign_module(
    tenant_id: str,
    module_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    取消租户的模块分配

    场景：取消模块分配
    WHEN 管理员请求 DELETE /tenant/admin/v1/tenants/{id}/modules/{moduleId}
    THEN 取消租户的模块分配

    场景：取消必须模块
    GIVEN 模块 is_need=true
    WHEN 管理员尝试取消
    THEN 返回 HTTP 400 错误

    场景：取消有用户使用的模块
    GIVEN 模块的角色正在被租户用户使用
    WHEN 管理员尝试取消
    THEN 返回 HTTP 400 错误，提示移除用户角色

    场景：取消未被分配的模块
    GIVEN 租户未分配该模块
    WHEN 管理员请求取消
    THEN 返回 HTTP 404 错误
    """
    try:
        success = await TenantModuleService.unassign_module(
            session,
            tenant_id=tenant_id,
            module_id=module_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not success:
        raise HTTPException(status_code=404, detail="租户未分配该模块")

    return ApiResponse.success(data=success)
