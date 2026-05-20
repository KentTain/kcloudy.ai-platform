"""
用户端租户控制器
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from demo.schemas.console.tenant import UserTenantVo, CurrentTenantVo, SwitchTenantVo
from demo.services.tenant_service import TenantService
from demo.models.tenant import TenantStatus
from framework.tenant.context import TenantContext, get_tenant_id, get_current_tenant
from framework.tenant.exceptions import TenantNotFoundError, TenantInactiveError

router = APIRouter()


def Success(data=None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


@router.get("")
async def list_user_tenants(user_id: str = "test_user") -> ORJSONResponse:
    """
    获取用户可用租户列表

    场景：获取用户可用租户列表
    WHEN 用户请求 GET /console/v1/tenants
    THEN 返回用户所属的所有租户列表

    场景：用户不属于任何租户
    WHEN 用户不属于任何租户时请求 GET /console/v1/tenants
    THEN 返回空列表
    """
    # TODO: 从认证信息获取用户 ID
    tenants = await TenantService.get_user_tenants(user_id)

    items = []
    for tenant in tenants:
        items.append(
            UserTenantVo(
                id=tenant.id,
                name=tenant.name,
                code=tenant.code,
                status=tenant.status,
                role="member",  # TODO: 从 UserTenant 获取实际角色
                is_default=False,  # TODO: 从 UserTenant 获取
            )
        )

    return ORJSONResponse(content=Success(items))


@router.get("/current")
async def get_current_tenant_info() -> ORJSONResponse:
    """
    获取当前租户信息

    场景：获取当前租户信息
    WHEN 用户请求 GET /console/v1/tenants/current
    THEN 返回当前租户的详细信息

    场景：未设置租户上下文
    WHEN 用户未设置租户上下文时请求 GET /console/v1/tenants/current
    THEN 返回 HTTP 400 错误
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="租户上下文未设置")

    tenant = await TenantService.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    return ORJSONResponse(
        content=Success(
            CurrentTenantVo(
                id=tenant.id,
                name=tenant.name,
                code=tenant.code,
                status=tenant.status,
            ).model_dump()
        )
    )


@router.post("/{tenant_id}/switch")
async def switch_tenant(
    tenant_id: str,
    user_id: str = "test_user",
) -> ORJSONResponse:
    """
    切换租户

    场景：切换到有权限的租户
    WHEN 用户请求 POST /console/v1/tenants/{id}/switch 且用户属于该租户
    THEN 返回包含新租户信息的 Token
    AND 后续请求使用新租户上下文

    场景：切换到无权限的租户
    WHEN 用户请求 POST /console/v1/tenants/{id}/switch 且用户不属于该租户
    THEN 返回 HTTP 403 错误，消息为 "无权访问该租户"

    场景：切换到不存在的租户
    WHEN 用户请求 POST /console/v1/tenants/nonexistent/switch
    THEN 返回 HTTP 404 错误

    场景：切换到已停用的租户
    WHEN 用户请求切换到状态为 `inactive` 的租户
    THEN 返回 HTTP 403 错误，消息为 "租户已停用"
    """
    # 检查租户是否存在
    tenant = await TenantService.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # 检查租户状态
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="租户已停用")

    # TODO: 检查用户是否有权访问该租户
    # user_tenants = await TenantService.get_user_tenants(user_id)
    # if tenant_id not in [t.id for t in user_tenants]:
    #     raise HTTPException(status_code=403, detail="无权访问该租户")

    # 设置新的租户上下文（实际应用中应该返回新的 Token）
    TenantContext.set_current_tenant(tenant)

    return ORJSONResponse(
        content=Success(
            SwitchTenantVo(
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                message="租户切换成功",
            ).model_dump()
        )
    )
