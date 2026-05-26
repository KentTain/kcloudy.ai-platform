"""
管理后台租户控制器
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import func, select

from framework.database.core.engine import async_session
from tenant.models import Tenant
from tenant.schemas.admin.tenant import (
    CacheConfigVo,
    DatabaseConfigVo,
    ResourceValidateVo,
    StorageConfigVo,
    TenantCreateRequest,
    TenantUpdateRequest,
    TenantVo,
    TenantListVo,
    TenantStatsVo,
    AdminLoginRequest,
    AdminLoginVo,
)
from tenant.services.tenant_service import TenantService
from tenant.middlewares.admin_auth_middleware import get_current_admin, AdminAuthService

router = APIRouter()


def Success(data=None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


def build_tenant_vo(tenant: Tenant) -> TenantVo:
    """构建租户响应对象"""
    database = None
    if tenant.db_name:
        database = DatabaseConfigVo(
            db_type=tenant.db_type,
            db_host=tenant.db_host,
            db_port=tenant.db_port,
            db_name=tenant.db_name,
            db_username=tenant.db_username,
        )

    storage = None
    if tenant.storage_bucket:
        storage = StorageConfigVo(
            storage_type=tenant.storage_type,
            storage_bucket=tenant.storage_bucket,
        )

    cache = None
    if tenant.cache_db is not None:
        cache = CacheConfigVo(cache_db=tenant.cache_db)

    return TenantVo(
        id=tenant.id,
        name=tenant.name,
        code=tenant.code,
        status=tenant.status,
        contact_name=tenant.contact_name,
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        expired_at=tenant.expired_at,
        settings=tenant.settings or {},
        database=database,
        storage=storage,
        cache=cache,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


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


@router.post("/tenants/validate/database")
async def validate_database_config(
    data: DatabaseConfigVo,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """验证数据库连接配置"""
    if not data.db_name:
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=True, message="使用默认数据库").model_dump())
        )

    if not all([data.db_type, data.db_host, data.db_port, data.db_username]):
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=False, message="数据库配置不完整").model_dump())
        )

    driver = "postgresql+asyncpg"
    if data.db_type == "mysql":
        driver = "mysql+aiomysql"
    elif data.db_type == "sqlite":
        driver = "sqlite+aiosqlite"

    # 验证接口不接收密码，无法真实连接，仅验证格式
    if data.db_type not in ("postgresql", "mysql", "sqlite"):
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=False, message="不支持的数据库类型").model_dump())
        )

    return ORJSONResponse(
        content=Success(ResourceValidateVo(valid=True, message="数据库配置格式有效").model_dump())
    )


@router.post("/tenants/validate/storage")
async def validate_storage_config(
    data: StorageConfigVo,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """验证存储桶配置"""
    if not data.storage_bucket:
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=True, message="使用默认存储桶").model_dump())
        )

    if data.storage_type and data.storage_type not in ("minio", "aliyun", "tencent", "local"):
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=False, message="不支持的存储类型").model_dump())
        )

    return ORJSONResponse(
        content=Success(ResourceValidateVo(valid=True, message="存储配置格式有效").model_dump())
    )


@router.post("/tenants/validate/cache")
async def validate_cache_config(
    data: CacheConfigVo,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """验证 Redis DB 配置"""
    if data.cache_db is None:
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=True, message="使用默认 Redis DB").model_dump())
        )

    if data.cache_db < 0 or data.cache_db > 15:
        return ORJSONResponse(
            content=Success(ResourceValidateVo(valid=False, message="Redis DB 编号必须在 0-15 范围内").model_dump())
        )

    # 检查是否已被其他租户使用
    async with async_session() as session:
        stmt = select(Tenant).where(Tenant.cache_db == data.cache_db)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return ORJSONResponse(
                content=Success(
                    ResourceValidateVo(
                        valid=False,
                        message=f"Redis DB {data.cache_db} 已被租户 {existing.code} 使用",
                    ).model_dump()
                )
            )

    return ORJSONResponse(
        content=Success(ResourceValidateVo(valid=True, message="缓存配置有效").model_dump())
    )


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
                items=[build_tenant_vo(t) for t in tenants],
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
        db_type=data.database.db_type if data.database else None,
        db_host=data.database.db_host if data.database else None,
        db_port=data.database.db_port if data.database else None,
        db_name=data.database.db_name if data.database else None,
        db_username=data.database.db_username if data.database else None,
        db_password=data.database.db_password if data.database else None,
        storage_type=data.storage.storage_type if data.storage else None,
        storage_bucket=data.storage.storage_bucket if data.storage else None,
        cache_db=data.cache.cache_db if data.cache else None,
    )

    return ORJSONResponse(
        content=Success(build_tenant_vo(tenant).model_dump())
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
        content=Success(build_tenant_vo(tenant).model_dump())
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
        db_type=data.database.db_type if data.database else None,
        db_host=data.database.db_host if data.database else None,
        db_port=data.database.db_port if data.database else None,
        db_name=data.database.db_name if data.database else None,
        db_username=data.database.db_username if data.database else None,
        db_password=data.database.db_password if data.database else None,
        storage_type=data.storage.storage_type if data.storage else None,
        storage_bucket=data.storage.storage_bucket if data.storage else None,
        cache_db=data.cache.cache_db if data.cache else None,
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(
        content=Success(build_tenant_vo(tenant).model_dump())
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
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.models import UserTenant

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
        content=Success(build_tenant_vo(tenant).model_dump())
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
        content=Success(build_tenant_vo(tenant).model_dump())
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
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.models import UserTenant

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
