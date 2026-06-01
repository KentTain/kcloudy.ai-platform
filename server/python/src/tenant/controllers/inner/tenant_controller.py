"""
Tenant 模块内部接口控制器

提供模块间内部调用接口，不对外暴露。
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field

from tenant.models import Tenant, TenantStatus
from tenant.services.tenant_service import TenantService

router = APIRouter()


def Success(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


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
    # 资源配置
    db_type: str | None = Field(None, description="数据库类型")
    db_host: str | None = Field(None, description="数据库主机")
    db_port: int | None = Field(None, description="数据库端口")
    db_name: str | None = Field(None, description="数据库名称")
    db_username: str | None = Field(None, description="数据库用户名")
    db_password: str | None = Field(None, description="数据库密码（解密后）")
    storage_type: str | None = Field(None, description="存储类型")
    storage_bucket: str | None = Field(None, description="存储桶名称")
    cache_db: int | None = Field(None, description="Redis DB 编号")
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
    """构建租户信息响应"""
    from framework.utils.crypto import decrypt

    db_password = None
    encryption_key = None

    if include_secrets:
        if tenant.db_password:
            try:
                db_password = decrypt(tenant.db_password)
            except Exception:
                pass
        if tenant.encryption_key:
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
        db_type=tenant.db_type,
        db_host=tenant.db_host,
        db_port=tenant.db_port,
        db_name=tenant.db_name,
        db_username=tenant.db_username,
        db_password=db_password,
        storage_type=tenant.storage_type,
        storage_bucket=tenant.storage_bucket,
        cache_db=tenant.cache_db,
        encryption_key=encryption_key,
        settings=tenant.settings or {},
    )


@router.get("/tenant/health")
async def health_check() -> ORJSONResponse:
    """
    健康检查端点

    场景：健康检查端点
    WHEN 请求 GET /inner/v1/tenant/health
    THEN 返回 {"status": "healthy"}
    AND 不依赖外部服务
    """
    return ORJSONResponse(content={"status": "healthy", "module": "tenant"})


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str) -> ORJSONResponse:
    """
    获取单个租户

    场景：获取单个租户
    WHEN 请求 GET /inner/v1/tenants/{tenant_id}
    THEN 返回指定租户的详细信息
    AND 不依赖 Token 认证
    AND tenant_id 由调用方显式传入

    场景：租户不存在
    WHEN 请求 GET /inner/v1/tenants/nonexistent
    THEN 返回 HTTP 404
    AND 响应体包含错误信息
    """
    tenant = await TenantService.get_by_id(tenant_id, use_cache=True)

    if not tenant:
        raise HTTPException(status_code=404, detail=f"租户 {tenant_id} 不存在")

    # 如果是 SimpleTenant（缓存），需要从数据库获取完整信息
    if not isinstance(tenant, Tenant):
        tenant = await TenantService.get_by_id(tenant_id, use_cache=False)
        if not tenant:
            raise HTTPException(status_code=404, detail=f"租户 {tenant_id} 不存在")

    return ORJSONResponse(
        content=Success(build_tenant_info(tenant, include_secrets=True).model_dump())
    )


@router.post("/tenants/batch")
async def get_tenants_batch(data: BatchTenantsRequest) -> ORJSONResponse:
    """
    批量获取租户

    场景：批量获取租户
    WHEN 请求 POST /inner/v1/tenants/batch
    WITH 请求体 {"tenant_ids": ["id1", "id2"]}
    THEN 返回多个租户的信息列表
    AND 返回顺序与请求顺序一致
    """
    tenants = await TenantService.get_tenants_batch(data.tenant_ids)

    return ORJSONResponse(
        content=Success(
            [
                build_tenant_info(t, include_secrets=True).model_dump()
                for t in tenants
                if t
            ]
        )
    )


@router.get("/tenants/{tenant_id}/validate")
async def validate_tenant_access(
    tenant_id: str,
    user_id: str,
) -> ORJSONResponse:
    """
    验证租户访问权限

    场景：验证租户访问权限
    WHEN 请求 GET /inner/v1/tenants/{tenant_id}/validate?user_id={user_id}
    THEN 返回布尔值表示用户是否有权访问该租户
    """
    # 检查租户是否存在且状态正常
    tenant = await TenantService.get_by_id(tenant_id)
    if not tenant:
        return ORJSONResponse(
            content=Success(
                ValidateAccessResponse(
                    valid=False,
                    tenant_id=tenant_id,
                    user_id=user_id,
                ).model_dump()
            )
        )

    if tenant.status != TenantStatus.ACTIVE:
        return ORJSONResponse(
            content=Success(
                ValidateAccessResponse(
                    valid=False,
                    tenant_id=tenant_id,
                    user_id=user_id,
                ).model_dump()
            )
        )

    # 检查用户是否属于该租户
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.services.user_service import UserService

    tenant_ids = await UserService.get_user_tenant_ids(user_id)
    if not tenant_ids:
        valid = False

    valid = tenant_id in tenant_ids

    return ORJSONResponse(
        content=Success(
            ValidateAccessResponse(
                valid=valid,
                tenant_id=tenant_id,
                user_id=user_id,
            ).model_dump()
        )
    )
