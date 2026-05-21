"""
管理后台租户控制器
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import func, select

from iam.models import Tenant, UserTenant
from framework.database.core.engine import async_session
from iam.schemas.admin.tenant import (
    TenantCreateRequest,
    TenantUpdateRequest,
    TenantVo,
    TenantListVo,
    TenantStatsVo,
    AdminLoginRequest,
    AdminLoginVo,
)
from iam.services.tenant_service import TenantService
from iam.middlewares.admin_auth_middleware import get_current_admin, AdminAuthService

router = APIRouter()


def Success(data=None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


# ============== 认证 API ==============

@router.post("/auth/login")
async def admin_login(data: AdminLoginRequest) -> ORJSONResponse:
    """
    管理员登录

    场景：管理员登录
    WHEN 超级管理员使用正确的用户名和密码登录
    THEN 返回管理员 Token
    """
    result = await AdminAuthService.login(data.username, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token, admin = result
    return ORJSONResponse(
        content=Success(
            AdminLoginVo(
                token=token,
                username=admin.username,
                is_default=admin.is_default,
            ).model_dump()
        )
    )


@router.post("/auth/logout")
async def admin_logout(request: Request, admin: dict = Depends(get_current_admin)) -> ORJSONResponse:
    """管理员登出"""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    if token:
        AdminAuthService.logout(token)
    return ORJSONResponse(content=Success())


# ============== 租户管理 API ==============

@router.get("/tenants")
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: str | None = None,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    查询租户列表

    场景：查询租户列表
    WHEN 管理员请求 GET /admin/v1/tenants
    THEN 返回所有租户列表（分页）

    场景：搜索租户
    WHEN 管理员请求 GET /admin/v1/tenants?keyword=acme
    THEN 返回名称或编码包含 "acme" 的租户列表
    """
    tenants, total = await TenantService.list_tenants(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
    )

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": TenantListVo(
                items=[TenantVo.model_validate(t) for t in tenants],
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump(),
        }
    )


@router.post("/tenants")
async def create_tenant(
    data: TenantCreateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    创建租户

    场景：创建租户
    WHEN 管理员请求 POST /admin/v1/tenants 并提供名称、编码
    THEN 创建新租户并返回租户信息

    场景：创建重复编码租户
    WHEN 管理员尝试创建已存在编码的租户
    THEN 返回 HTTP 400 错误，消息为 "租户编码已存在"
    """
    # 检查编码是否已存在
    existing = await TenantService.get_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="租户编码已存在")

    tenant = await TenantService.create(
        name=data.name,
        code=data.code,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        expired_at=data.expired_at,
        settings=data.settings,
    )

    return ORJSONResponse(
        content=Success(TenantVo.model_validate(tenant).model_dump())
    )


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    查询租户详情

    场景：查询租户详情
    WHEN 管理员请求 GET /admin/v1/tenants/{id}
    THEN 返回租户详细信息

    场景：查询不存在的租户
    WHEN 管理员请求 GET /admin/v1/tenants/nonexistent
    THEN 返回 HTTP 404 错误
    """
    tenant = await TenantService.get_by_id(tenant_id, use_cache=False)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(
        content=Success(TenantVo.model_validate(tenant).model_dump())
    )


@router.put("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    data: TenantUpdateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    更新租户

    场景：更新租户
    WHEN 管理员请求 PUT /admin/v1/tenants/{id} 并提供更新数据
    THEN 更新租户信息并返回更新后的数据
    """
    tenant = await TenantService.update(
        tenant_id=tenant_id,
        name=data.name,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        expired_at=data.expired_at,
        settings=data.settings,
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(
        content=Success(TenantVo.model_validate(tenant).model_dump())
    )


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    删除租户

    场景：删除租户
    WHEN 管理员请求 DELETE /admin/v1/tenants/{id}
    THEN 删除租户（软删除）

    场景：删除有用户的租户
    WHEN 管理员尝试删除有用户关联的租户
    THEN 返回 HTTP 400 错误，消息为 "租户下存在用户，无法删除"
    """
    # 检查租户下是否有用户
    async with async_session() as session:
        stmt = select(func.count(UserTenant.id)).where(UserTenant.tenant_id == tenant_id)
        result = await session.execute(stmt)
        user_count = result.scalar() or 0

        if user_count > 0:
            raise HTTPException(status_code=400, detail="租户下存在用户，无法删除")

    success = await TenantService.delete(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(content=Success())


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    激活租户

    场景：激活租户
    WHEN 管理员请求 POST /admin/v1/tenants/{id}/activate
    THEN 租户状态变为 `active`
    """
    tenant = await TenantService.activate(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(
        content=Success(TenantVo.model_validate(tenant).model_dump())
    )


@router.post("/tenants/{tenant_id}/deactivate")
async def deactivate_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    停用租户

    场景：停用租户
    WHEN 管理员请求 POST /admin/v1/tenants/{id}/deactivate
    THEN 租户状态变为 `inactive`
    """
    tenant = await TenantService.deactivate(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(
        content=Success(TenantVo.model_validate(tenant).model_dump())
    )


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    查询租户统计

    场景：查询租户统计
    WHEN 管理员请求 GET /admin/v1/tenants/{id}/stats
    THEN 返回租户统计信息（用户数、存储用量等）
    """
    tenant = await TenantService.get_by_id(tenant_id, use_cache=False)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # 统计用户数
    async with async_session() as session:
        stmt = select(func.count(UserTenant.id)).where(UserTenant.tenant_id == tenant_id)
        result = await session.execute(stmt)
        user_count = result.scalar() or 0

    stats = TenantStatsVo(
        tenant_id=tenant_id,
        user_count=user_count,
        storage_usage=0,  # TODO: 实现存储用量统计
        active_users=0,   # TODO: 实现活跃用户统计
    )

    return ORJSONResponse(content=Success(stats.model_dump()))
