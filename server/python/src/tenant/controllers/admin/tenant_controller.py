"""
管理后台租户控制器
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra
from tenant.middlewares.admin_auth_middleware import AdminAuthService, get_current_admin
from tenant.models import ModuleMenu, Tenant
from tenant.schemas.admin.module import ModuleMenuTreeResponse
from tenant.schemas.admin.tenant import (
    AdminLoginRequest,
    AdminLoginResponse,
    ResourceBindingRequest,
    ResourceBindingResponse,
    ResourceConfigReferenceResponse,
    TenantCreate,
    TenantListStats,
    TenantResponse,
    TenantStatsResponse,
    TenantUpdate,
)
from tenant.services.module_menu_service import ModuleMenuService
from tenant.services.module_service import ModuleService
from tenant.services.tenant_service import TenantService

router = APIRouter()


async def _get_resource_ref(
    session: AsyncSession,
    config_id: str | None,
    service,
) -> ResourceConfigReferenceResponse | None:
    """获取资源配置引用"""
    if not config_id:
        return None
    config = await service.get_by_id(session, config_id)
    return ResourceConfigReferenceResponse.from_config(config)


async def build_tenant_vo(session: AsyncSession, tenant: Tenant) -> TenantResponse:
    """构建租户响应对象"""
    from tenant.services import (
        CacheConfigService,
        DatabaseConfigService,
        PubSubConfigService,
        QueueConfigService,
        StorageConfigService,
    )

    # 顺序查询 5 个资源配置，避免 SQLAlchemy Session 并发问题
    db_ref = await _get_resource_ref(session, tenant.db_config_id, DatabaseConfigService)
    storage_ref = await _get_resource_ref(session, tenant.storage_config_id, StorageConfigService)
    cache_ref = await _get_resource_ref(session, tenant.cache_config_id, CacheConfigService)
    queue_ref = await _get_resource_ref(session, tenant.queue_config_id, QueueConfigService)
    pubsub_ref = await _get_resource_ref(session, tenant.pubsub_config_id, PubSubConfigService)

    return TenantResponse.from_tenant(
        tenant=tenant,
        db_config=db_ref,
        storage_config=storage_ref,
        cache_config=cache_ref,
        queue_config=queue_ref,
        pubsub_config=pubsub_ref,
    )


async def build_tenant_vos_batch(
    session: AsyncSession, tenants: list[Tenant]
) -> list[TenantResponse]:
    """
    批量构建租户响应对象（优化版，避免 N+1 查询）

    Args:
        session: 数据库会话
        tenants: 租户列表

    Returns:
        list[TenantResponse]: 租户响应列表
    """
    if not tenants:
        return []

    from tenant.models import (
        CacheConfig,
        DatabaseConfig,
        PubSubConfig,
        QueueConfig,
        StorageConfig,
    )

    # 1. 收集所有 config_ids
    db_config_ids = {t.db_config_id for t in tenants if t.db_config_id}
    storage_config_ids = {t.storage_config_id for t in tenants if t.storage_config_id}
    cache_config_ids = {t.cache_config_id for t in tenants if t.cache_config_id}
    queue_config_ids = {t.queue_config_id for t in tenants if t.queue_config_id}
    pubsub_config_ids = {t.pubsub_config_id for t in tenants if t.pubsub_config_id}

    # 2. 批量查询所有配置
    db_configs = {}
    if db_config_ids:
        stmt = select(DatabaseConfig).where(DatabaseConfig.id.in_(db_config_ids))
        result = await session.execute(stmt)
        for c in result.scalars().all():
            db_configs[c.id] = ResourceConfigReferenceResponse.from_config(c)

    storage_configs = {}
    if storage_config_ids:
        stmt = select(StorageConfig).where(StorageConfig.id.in_(storage_config_ids))
        result = await session.execute(stmt)
        for c in result.scalars().all():
            storage_configs[c.id] = ResourceConfigReferenceResponse.from_config(c)

    cache_configs = {}
    if cache_config_ids:
        stmt = select(CacheConfig).where(CacheConfig.id.in_(cache_config_ids))
        result = await session.execute(stmt)
        for c in result.scalars().all():
            cache_configs[c.id] = ResourceConfigReferenceResponse.from_config(c)

    queue_configs = {}
    if queue_config_ids:
        stmt = select(QueueConfig).where(QueueConfig.id.in_(queue_config_ids))
        result = await session.execute(stmt)
        for c in result.scalars().all():
            queue_configs[c.id] = ResourceConfigReferenceResponse.from_config(c)

    pubsub_configs = {}
    if pubsub_config_ids:
        stmt = select(PubSubConfig).where(PubSubConfig.id.in_(pubsub_config_ids))
        result = await session.execute(stmt)
        for c in result.scalars().all():
            pubsub_configs[c.id] = ResourceConfigReferenceResponse.from_config(c)

    # 3. 组装 TenantResponse
    result = []
    for t in tenants:
        vo = TenantResponse.from_tenant(
            tenant=t,
            db_config=db_configs.get(t.db_config_id),
            storage_config=storage_configs.get(t.storage_config_id),
            cache_config=cache_configs.get(t.cache_config_id),
            queue_config=queue_configs.get(t.queue_config_id),
            pubsub_config=pubsub_configs.get(t.pubsub_config_id),
        )
        result.append(vo)

    return result


# ============== 认证 API ==============


@router.post("/auth/login")
async def admin_login(
    data: AdminLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    管理员登录

    场景：管理员登录
    WHEN 超级管理员使用正确的用户名和密码登录
    THEN 返回管理员 Token
    """
    result = await AdminAuthService.login(session, data.username, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token, admin = result
    return Success(
        data=AdminLoginResponse(
            token=token,
            username=admin.username,
            is_default=admin.is_default,
        ).model_dump()
    )


@router.post("/auth/logout")
async def admin_logout(
    request: Request, admin: dict = Depends(get_current_admin)
) -> ORJSONResponse:
    """管理员登出"""
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.replace("Bearer ", "")
        if auth_header.startswith("Bearer ")
        else None
    )
    if token:
        AdminAuthService.logout(token)
    return Success(data=True)


# ============== 租户管理 API ==============


@router.get("/tenants")
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询租户列表

    场景：查询租户列表
    WHEN 管理员请求 GET /tenant/admin/v1/tenants
    THEN 返回所有租户列表（分页）

    场景：搜索租户
    WHEN 管理员请求 GET /tenant/admin/v1/tenants?keyword=acme
    THEN 返回名称或编码包含 "acme" 的租户列表
    """
    # 顺序查询，避免 SQLAlchemy Session 并发问题
    result = await TenantService.list_tenants(
        session,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
    )
    tenants, total = result

    stats = await TenantService.get_tenant_stats(session)

    # 批量构建 TenantResponse（避免 N+1 查询）
    tenant_vos = await build_tenant_vos_batch(session, tenants)

    return SuccessExtra(
        data=tenant_vos,
        total=total,
        page=page,
        page_size=page_size,
        stats=TenantListStats(**stats),
    )


@router.post("/tenants")
async def create_tenant(
    data: TenantCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建租户

    场景：创建租户
    WHEN 管理员请求 POST /tenant/admin/v1/tenants 并提供名称、编码
    THEN 创建新租户并返回租户信息

    场景：创建重复编码租户
    WHEN 管理员尝试创建已存在编码的租户
    THEN 返回 HTTP 400 错误，消息为 "租户编码已存在"
    """
    # 检查编码是否已存在
    existing = await TenantService.get_by_code(session, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="租户编码已存在")

    tenant = await TenantService.create(
        session,
        name=data.name,
        code=data.code,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        expired_at=data.expired_at,
        settings=data.settings,
        db_config_id=data.db_config_id,
        storage_config_id=data.storage_config_id,
        cache_config_id=data.cache_config_id,
        queue_config_id=data.queue_config_id,
        pubsub_config_id=data.pubsub_config_id,
    )

    return Success(data=(await build_tenant_vo(session, tenant)).model_dump())


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询租户详情

    场景：查询租户详情
    WHEN 管理员请求 GET /tenant/admin/v1/tenants/{id}
    THEN 返回租户详细信息

    场景：查询不存在的租户
    WHEN 管理员请求 GET /tenant/admin/v1/tenants/nonexistent
    THEN 返回 HTTP 404 错误
    """
    tenant = await TenantService.get_by_id(session, tenant_id, use_cache=False)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # get_by_id 返回的是 SimpleTenant，需要重新获取 ORM 模型来构建完整的 VO
    tenant_model = await TenantService.get_resource_bindings(session, tenant_id)
    return Success(data=(await build_tenant_vo(session, tenant_model)).model_dump())


@router.put("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新租户

    场景：更新租户
    WHEN 管理员请求 PUT /tenant/admin/v1/tenants/{id} 并提供更新数据
    THEN 更新租户信息并返回更新后的数据
    """
    tenant = await TenantService.update(
        session,
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

    return Success(data=(await build_tenant_vo(session, tenant)).model_dump())


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除租户

    场景：删除租户
    WHEN 管理员请求 DELETE /tenant/admin/v1/tenants/{id}
    THEN 删除租户（软删除）

    场景：删除有用户的租户
    WHEN 管理员尝试删除有用户关联的租户
    THEN 返回 HTTP 400 错误，消息为 "租户下存在用户，无法删除"
    """
    # 检查租户下是否有用户
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_ids = await iam_client.get_tenant_user_ids(session, tenant_id)
    if len(user_ids) > 0:
        raise HTTPException(status_code=400, detail="租户下存在用户，无法删除")

    success = await TenantService.delete(session, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="租户不存在")

    return Success(data=success)


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    激活租户

    场景：激活租户
    WHEN 管理员请求 POST /tenant/admin/v1/tenants/{id}/activate
    THEN 租户状态变为 `active`
    """
    tenant = await TenantService.activate(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return Success(data=(await build_tenant_vo(session, tenant)).model_dump())


@router.post("/tenants/{tenant_id}/deactivate")
async def deactivate_tenant(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    停用租户

    场景：停用租户
    WHEN 管理员请求 POST /tenant/admin/v1/tenants/{id}/deactivate
    THEN 租户状态变为 `inactive`
    """
    tenant = await TenantService.deactivate(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return Success(data=(await build_tenant_vo(session, tenant)).model_dump())


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询租户统计

    场景：查询租户统计
    WHEN 管理员请求 GET /tenant/admin/v1/tenants/{id}/stats
    THEN 返回租户统计信息（用户数、存储用量等）
    """
    tenant = await TenantService.get_by_id(session, tenant_id, use_cache=False)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # 统计用户数
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_ids = await iam_client.get_tenant_user_ids(session, tenant_id)
    user_count = len(user_ids)

    stats = TenantStatsResponse(
        tenant_id=tenant_id,
        user_count=user_count,
        storage_usage=0,  # TODO: 实现存储用量统计
        active_users=0,  # TODO: 实现活跃用户统计
    )

    return Success(data=stats.model_dump())


# ============== 资源绑定 API ==============


@router.get("/tenants/{tenant_id}/resources")
async def get_tenant_resources(
    tenant_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取租户资源绑定

    场景：查询资源绑定
    WHEN 管理员请求 GET /tenant/admin/v1/tenants/{id}/resources
    THEN 返回租户当前的资源绑定情况
    """
    tenant = await TenantService.get_resource_bindings(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    from tenant.services import (
        CacheConfigService,
        DatabaseConfigService,
        PubSubConfigService,
        QueueConfigService,
        StorageConfigService,
    )

    # 顺序查询 5 个资源配置，避免 SQLAlchemy Session 并发问题
    db_ref = await _get_resource_ref(session, tenant.db_config_id, DatabaseConfigService)
    storage_ref = await _get_resource_ref(session, tenant.storage_config_id, StorageConfigService)
    cache_ref = await _get_resource_ref(session, tenant.cache_config_id, CacheConfigService)
    queue_ref = await _get_resource_ref(session, tenant.queue_config_id, QueueConfigService)
    pubsub_ref = await _get_resource_ref(session, tenant.pubsub_config_id, PubSubConfigService)

    return Success(
        data=ResourceBindingResponse(
            tenant_id=tenant.id,
            db_config=db_ref,
            storage_config=storage_ref,
            cache_config=cache_ref,
            queue_config=queue_ref,
            pubsub_config=pubsub_ref,
        ).model_dump()
    )


@router.put("/tenants/{tenant_id}/resources")
async def update_tenant_resources(
    tenant_id: str,
    data: ResourceBindingRequest,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新租户资源绑定

    场景：资源绑定
    WHEN 管理员请求 PUT /tenant/admin/v1/tenants/{id}/resources 并提供配置 ID
    THEN 更新租户的资源绑定

    场景：解绑资源
    WHEN 管理员将某个配置设为 null
    THEN 解除该资源的绑定
    """
    from tenant.services import (
        CacheConfigService,
        DatabaseConfigService,
        PubSubConfigService,
        QueueConfigService,
        StorageConfigService,
    )

    # 引用校验：绑定的配置 ID 必须存在
    async def _validate_config(
        sess: AsyncSession, config_id: str | None, service, config_type: str
    ):
        if config_id is not None:
            config = await service.get_by_id(sess, config_id)
            if not config:
                raise HTTPException(
                    status_code=404,
                    detail=f"{config_type}配置不存在: {config_id}",
                )

    # 使用 asyncio.gather 并行校验 5 个配置
    await asyncio.gather(
        _validate_config(session, data.db_config_id, DatabaseConfigService, "数据库"),
        _validate_config(session, data.storage_config_id, StorageConfigService, "存储"),
        _validate_config(session, data.cache_config_id, CacheConfigService, "缓存"),
        _validate_config(session, data.queue_config_id, QueueConfigService, "队列"),
        _validate_config(
            session, data.pubsub_config_id, PubSubConfigService, "发布订阅"
        ),
    )

    # 更新资源绑定
    tenant = await TenantService.update_resource_bindings(
        session,
        tenant_id=tenant_id,
        db_config_id=data.db_config_id,
        storage_config_id=data.storage_config_id,
        cache_config_id=data.cache_config_id,
        queue_config_id=data.queue_config_id,
        pubsub_config_id=data.pubsub_config_id,
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # 顺序查询 5 个资源配置，避免 SQLAlchemy Session 并发问题
    db_ref = await _get_resource_ref(session, tenant.db_config_id, DatabaseConfigService)
    storage_ref = await _get_resource_ref(session, tenant.storage_config_id, StorageConfigService)
    cache_ref = await _get_resource_ref(session, tenant.cache_config_id, CacheConfigService)
    queue_ref = await _get_resource_ref(session, tenant.queue_config_id, QueueConfigService)
    pubsub_ref = await _get_resource_ref(session, tenant.pubsub_config_id, PubSubConfigService)

    return Success(
        data=ResourceBindingResponse(
            tenant_id=tenant.id,
            db_config=db_ref,
            storage_config=storage_ref,
            cache_config=cache_ref,
            queue_config=queue_ref,
            pubsub_config=pubsub_ref,
        ).model_dump()
    )


# ============== 管理后台菜单 API ==============


def _build_menu_item_from_dict(menu: ModuleMenu) -> ModuleMenuTreeResponse | None:
    """将菜单 ModuleMenu 对象转换为 ModuleMenuTreeResponse（仅处理二级菜单项）"""
    if not menu.is_visible:
        return None

    return ModuleMenuTreeResponse(
        id=menu.id,
        module_id=menu.module_id,
        parent_id=menu.parent_id,
        code=menu.code,
        name=menu.name,
        path=menu.path,
        icon=menu.icon,
        sort_order=menu.sort_order,
        is_visible=menu.is_visible,
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=[],  # 二级菜单无子菜单
    )


@router.get("/admin/menus")
async def get_admin_menus(
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取管理员菜单（二级结构）

    菜单结构：
    - 一级菜单：模块菜单（来自 modules 表，无路由，不可点击）
    - 二级菜单：功能菜单（来自 module_menus 表，有路由）

    场景：成功获取菜单
    WHEN 管理员请求 GET /tenant/admin/v1/admin/menus
    THEN 返回所有活跃模块及其功能菜单的树形结构

    场景：无活跃模块
    WHEN 数据库中没有活跃模块
    THEN 返回空数组
    """

    # 获取租户模块（一级菜单）
    module = await ModuleService.get_by_code(session, "tenant")

    if not module:
        return Success(data=[])

    result: list[ModuleMenuTreeResponse] = []

    # 获取该模块的功能菜单（二级菜单）
    menus = await ModuleMenuService.list_menus(session, module.id)

    # 过滤不可见菜单，转换为响应模型
    visible_menus = [_build_menu_item_from_dict(m) for m in menus]
    visible_menus = [m for m in visible_menus if m is not None]

    # 构建一级模块菜单
    module_menu = ModuleMenuTreeResponse(
        id=module.id,
        module_id=module.id,
        parent_id=None,
        code=module.code,
        name=module.name,
        path="",  # 模块菜单无路由
        icon=module.icon,
        sort_order=0,
        is_visible=True,
        created_at=module.created_at,
        updated_at=module.updated_at,
        children=visible_menus,
    )

    result.append(module_menu)

    return Success(data=[r.model_dump() for r in result])
