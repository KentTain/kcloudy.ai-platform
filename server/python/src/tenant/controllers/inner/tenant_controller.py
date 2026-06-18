"""
Tenant 模块内部接口控制器

提供模块间内部调用接口，不对外暴露。
"""

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra
from framework.tenant.context import SimpleTenant
from tenant.models import Tenant, TenantStatus
from tenant.services.tenant_service import TenantService

router = APIRouter()


class ResourceConfigInfo(BaseModel):
    """资源配置信息"""

    id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")


class TenantDatabaseConfigInfo(BaseModel):
    """数据库配置信息（含连接参数）"""

    type: str = Field(..., description="数据库类型")
    host: str = Field(..., description="数据库主机")
    port: int = Field(..., description="数据库端口")
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: str | None = Field(None, description="数据库密码（解密后）")


class TenantStorageConfigInfo(BaseModel):
    """存储配置信息"""

    type: str = Field(..., description="存储类型")
    endpoint: str = Field(..., description="服务端点")
    bucket: str = Field(..., description="存储桶名称")
    access_key: str = Field(..., description="访问密钥")
    secret_key: str | None = Field(None, description="私密密钥（解密后）")


class TenantCacheConfigInfo(BaseModel):
    """缓存配置信息"""

    host: str = Field(..., description="缓存主机")
    port: int = Field(..., description="缓存端口")
    password: str | None = Field(None, description="缓存密码（解密后）")
    db: int = Field(..., description="数据库编号")
    prefix: str = Field(..., description="键前缀")


class TenantQueueConfigInfo(BaseModel):
    """队列配置信息"""

    type: str = Field(..., description="队列类型")
    host: str = Field(..., description="队列主机")
    port: int = Field(..., description="队列端口")
    username: str | None = Field(None, description="用户名")
    password: str | None = Field(None, description="密码（解密后）")
    vhost: str = Field(..., description="虚拟主机")


class TenantPubSubConfigInfo(BaseModel):
    """发布订阅配置信息"""

    type: str = Field(..., description="发布订阅类型")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    username: str | None = Field(None, description="用户名")
    password: str | None = Field(None, description="密码（解密后）")


class TenantInfoResponse(BaseModel):
    """租户信息响应"""

    id: str = Field(..., description="租户ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    status: str = Field(..., description="状态")
    contact_name: str | None = Field(None, description="联系人姓名")
    contact_email: str | None = Field(None, description="联系人邮箱")
    contact_phone: str | None = Field(None, description="联系人电话")
    expired_at: str | None = Field(None, description="过期时间")
    # 资源配置 ID
    db_config_id: str | None = Field(None, description="数据库配置ID")
    storage_config_id: str | None = Field(None, description="存储配置ID")
    cache_config_id: str | None = Field(None, description="缓存配置ID")
    queue_config_id: str | None = Field(None, description="队列配置ID")
    pubsub_config_id: str | None = Field(None, description="发布订阅配置ID")
    # 敏感信息
    encryption_key: str | None = Field(None, description="租户加密密钥（解密后）")
    settings: dict[str, Any] = Field(default_factory=dict, description="扩展设置")


class TenantFullInfoResponse(BaseModel):
    """租户完整信息响应（含资源配置详情）"""

    id: str = Field(..., description="租户ID")
    name: str = Field(..., description="租户名称")
    code: str = Field(..., description="租户编码")
    status: str = Field(..., description="状态")
    contact_name: str | None = Field(None, description="联系人姓名")
    contact_email: str | None = Field(None, description="联系人邮箱")
    contact_phone: str | None = Field(None, description="联系人电话")
    expired_at: str | None = Field(None, description="过期时间")
    # 资源配置详情
    database: TenantDatabaseConfigInfo | None = Field(None, description="数据库配置")
    storage: TenantStorageConfigInfo | None = Field(None, description="存储配置")
    cache: TenantCacheConfigInfo | None = Field(None, description="缓存配置")
    queue: TenantQueueConfigInfo | None = Field(None, description="队列配置")
    pubsub: TenantPubSubConfigInfo | None = Field(None, description="发布订阅配置")
    # 敏感信息
    encryption_key: str | None = Field(None, description="租户加密密钥（解密后）")
    settings: dict[str, Any] = Field(default_factory=dict, description="扩展设置")


class BatchTenantsRequest(BaseModel):
    """批量获取租户请求"""

    tenant_ids: list[str] = Field(..., description="租户ID列表")


class ValidateAccessResponse(BaseModel):
    """验证访问权限响应"""

    valid: bool = Field(..., description="是否有权访问")
    tenant_id: str = Field(..., description="租户ID")
    user_id: str = Field(..., description="用户ID")


def build_tenant_info(
    tenant: Tenant, include_secrets: bool = False
) -> TenantInfoResponse:
    """构建租户基础信息响应"""
    from framework.utils.crypto import decrypt

    encryption_key = None
    if include_secrets and tenant.encryption_key:
        try:
            encryption_key = decrypt(tenant.encryption_key)
        except Exception:
            pass

    return TenantInfoResponse(
        id=tenant.id,
        name=tenant.name,
        code=tenant.code,
        status=tenant.status,
        contact_name=tenant.contact_name,
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        expired_at=tenant.expired_at.isoformat() if tenant.expired_at else None,
        db_config_id=tenant.db_config_id,
        storage_config_id=tenant.storage_config_id,
        cache_config_id=tenant.cache_config_id,
        queue_config_id=tenant.queue_config_id,
        pubsub_config_id=tenant.pubsub_config_id,
        encryption_key=encryption_key,
        settings=tenant.settings or {},
    )


def build_tenant_full_info(simple_tenant: SimpleTenant) -> TenantFullInfoResponse:
    """构建租户完整信息响应（含资源配置详情）"""
    from framework.utils.crypto import decrypt

    encryption_key = None
    # SimpleTenant 没有 encryption_key，需要从原始模型获取
    # 这里暂时返回 None，如果需要可以在调用方传入

    database = None
    if simple_tenant.database:
        database = TenantDatabaseConfigInfo(
            type=simple_tenant.database.type.value,
            host=simple_tenant.database.host,
            port=simple_tenant.database.port,
            database=simple_tenant.database.database,
            username=simple_tenant.database.username,
            password=simple_tenant.database.password or None,
        )

    storage = None
    if simple_tenant.storage:
        storage = TenantStorageConfigInfo(
            type=simple_tenant.storage.type.value,
            endpoint=simple_tenant.storage.endpoint,
            bucket=simple_tenant.storage.bucket,
            access_key=simple_tenant.storage.access_key,
            secret_key=simple_tenant.storage.secret_key or None,
        )

    cache = None
    if simple_tenant.cache:
        cache = TenantCacheConfigInfo(
            host=simple_tenant.cache.host,
            port=simple_tenant.cache.port,
            password=simple_tenant.cache.password or None,
            db=simple_tenant.cache.db,
            prefix=simple_tenant.cache.prefix,
        )

    queue = None
    if simple_tenant.queue:
        queue = TenantQueueConfigInfo(
            type=simple_tenant.queue.type.value,
            host=simple_tenant.queue.host,
            port=simple_tenant.queue.port,
            username=simple_tenant.queue.username or None,
            password=simple_tenant.queue.password or None,
            vhost=simple_tenant.queue.vhost,
        )

    pubsub = None
    if simple_tenant.pubsub:
        pubsub = TenantPubSubConfigInfo(
            type=simple_tenant.pubsub.type.value,
            host=simple_tenant.pubsub.host,
            port=simple_tenant.pubsub.port,
            username=simple_tenant.pubsub.username or None,
            password=simple_tenant.pubsub.password or None,
        )

    return TenantFullInfoResponse(
        id=simple_tenant.id,
        name=simple_tenant.name,
        code=simple_tenant.code,
        status=simple_tenant.status,
        contact_name=simple_tenant.contact_name,
        contact_email=simple_tenant.contact_email,
        contact_phone=simple_tenant.contact_phone,
        expired_at=simple_tenant.expired_at.isoformat()
        if simple_tenant.expired_at
        else None,
        database=database,
        storage=storage,
        cache=cache,
        queue=queue,
        pubsub=pubsub,
        encryption_key=encryption_key,
        settings=getattr(simple_tenant, "settings", {}),
    )


@router.get("/health")
async def health_check() -> ORJSONResponse:
    """
    健康检查端点

    场景：健康检查端点
    WHEN 请求 GET /tenant/inner/v1/health
    THEN 返回 {"status": "healthy"}
    AND 不依赖外部服务
    """
    return ORJSONResponse(content={"status": "healthy", "module": "tenant"})


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取单个租户（含完整资源配置）

    场景：获取单个租户
    WHEN 请求 GET /tenant/inner/v1/tenants/{tenant_id}
    THEN 返回指定租户的详细信息
    AND 不依赖 Token 认证
    AND tenant_id 由调用方显式传入

    场景：租户不存在
    WHEN 请求 GET /tenant/inner/v1/tenants/nonexistent
    THEN 返回 HTTP 404
    AND 响应体包含错误信息
    """
    simple_tenant = await TenantService.get_by_id(session, tenant_id, use_cache=True)

    if not simple_tenant:
        raise HTTPException(status_code=404, detail=f"租户 {tenant_id} 不存在")

    return Success(data=build_tenant_full_info(simple_tenant).model_dump())


@router.get("/tenants/{tenant_id}/basic")
async def get_tenant_basic(
    tenant_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取租户基础信息（不含资源配置详情）

    场景：获取租户基础信息
    WHEN 请求 GET /tenant/inner/v1/tenants/{tenant_id}/basic
    THEN 返回租户基础信息和资源配置 ID
    """
    tenant = await TenantService.get_resource_bindings(session, tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail=f"租户 {tenant_id} 不存在")

    return Success(data=build_tenant_info(tenant, include_secrets=False).model_dump())


@router.post("/tenants/batch")
async def get_tenants_batch(
    data: BatchTenantsRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    批量获取租户

    场景：批量获取租户
    WHEN 请求 POST /tenant/inner/v1/tenants/batch
    WITH 请求体 {"tenant_ids": ["id1", "id2"]}
    THEN 返回多个租户的信息列表
    AND 返回顺序与请求顺序一致
    """
    tenants = await TenantService.get_tenants_batch(session, data.tenant_ids)

    return Success(
        data=[
            build_tenant_info(t, include_secrets=False).model_dump()
            for t in tenants
            if t
        ]
    )


@router.post("/tenants/batch-full")
async def get_tenants_batch_full(
    data: BatchTenantsRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    批量获取租户完整信息（含资源配置详情）

    场景：批量获取租户完整信息
    WHEN 请求 POST /tenant/inner/v1/tenants/batch-full
    WITH 请求体 {"tenant_ids": ["id1", "id2"]}
    THEN 返回多个租户的完整信息列表（含资源配置）
    """
    tenants = await TenantService.get_tenants_batch(session, data.tenant_ids)
    simple_tenants = await asyncio.gather(
        *[
            TenantService.build_simple_tenant(session, t)
            for t in tenants
            if t is not None
        ]
    )

    return Success(
        data=[build_tenant_full_info(st).model_dump() for st in simple_tenants]
    )


@router.get("/tenants/{tenant_id}/validate")
async def validate_tenant_access(
    tenant_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    验证租户访问权限

    场景：验证租户访问权限
    WHEN 请求 GET /tenant/inner/v1/tenants/{tenant_id}/validate?user_id={user_id}
    THEN 返回布尔值表示用户是否有权访问该租户
    """
    simple_tenant = await TenantService.get_by_id(session, tenant_id)
    if not simple_tenant:
        return Success(
            data=ValidateAccessResponse(
                valid=False,
                tenant_id=tenant_id,
                user_id=user_id,
            ).model_dump()
        )

    if simple_tenant.status != TenantStatus.ACTIVE:
        return Success(
            data=ValidateAccessResponse(
                valid=False,
                tenant_id=tenant_id,
                user_id=user_id,
            ).model_dump()
        )

    # 检查用户是否属于该租户
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_tenants = await iam_client.get_user_tenants(session, user_id)
    tenant_ids = [ut.tenant_id for ut in user_tenants]
    valid = tenant_id in tenant_ids

    return Success(
        data=ValidateAccessResponse(
            valid=valid,
            tenant_id=tenant_id,
            user_id=user_id,
        ).model_dump()
    )
