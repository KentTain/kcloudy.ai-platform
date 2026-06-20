"""
IAM 模块内部接口控制器

提供模块间内部调用接口，不对外暴露。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.models import User, UserOrganization, UserTenant
from iam.services.organization_service import OrganizationService
from iam.services.user_service import UserService

router = APIRouter()


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")
    nickname: str | None = Field(None, description="昵称")
    avatar: str | None = Field(None, description="头像")
    status: str = Field(..., description="状态")
    tenant_id: str | None = Field(None, description="当前租户ID")


class BatchUsersRequest(BaseModel):
    """批量获取用户请求"""
    user_ids: list[str] = Field(..., description="用户ID列表")


class OrganizationInfoInnerResponse(BaseModel):
    """组织信息响应"""
    id: str = Field(..., description="组织ID")
    name: str = Field(..., description="组织名称")
    parent_id: str | None = Field(None, description="父组织ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")


class UserOrganizationResponse(BaseModel):
    """用户组织响应"""
    user_id: str = Field(..., description="用户ID")
    organizations: list[OrganizationInfoInnerResponse] = Field(default_factory=list, description="组织列表")


class OrganizationTreeInnerResponse(BaseModel):
    """组织树响应"""
    id: str = Field(..., description="组织ID")
    name: str = Field(..., description="组织名称")
    parent_id: str | None = Field(None, description="父组织ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")
    children: list["OrganizationTreeInnerResponse"] = Field(default_factory=list, description="子组织")


class UserTenantInfo(BaseModel):
    """用户-租户关联信息"""
    tenant_id: str = Field(..., description="租户ID")
    role: str = Field(..., description="角色")
    is_default: bool = Field(..., description="是否默认租户")


class UserTenantsResponse(BaseModel):
    """用户租户列表响应"""
    user_id: str = Field(..., description="用户ID")
    tenants: list[UserTenantInfo] = Field(default_factory=list, description="租户列表")


class TenantUsersResponse(BaseModel):
    """租户用户列表响应"""
    tenant_id: str = Field(..., description="租户ID")
    user_ids: list[str] = Field(default_factory=list, description="用户ID列表")


def build_user_info(user: User, tenant_id: str | None = None) -> UserInfoResponse:
    """构建用户信息响应"""
    return UserInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar=user.avatar,
        status=user.status,
        tenant_id=tenant_id,
    )


@router.get("/health")
async def health_check() -> ORJSONResponse:
    """
    健康检查端点

    场景：健康检查端点
    WHEN 请求 GET /iam/inner/v1/health
    THEN 返回 {"status": "healthy"}
    """
    return ORJSONResponse(content={"status": "healthy", "module": "iam"})


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取单个用户

    场景：获取单个用户
    WHEN 请求 GET /iam/inner/v1/users/{user_id}
    THEN 返回指定用户的详细信息
    AND 不依赖 Token 认证
    AND user_id 由调用方显式传入

    场景：用户不存在
    WHEN 请求 GET /iam/inner/v1/users/nonexistent
    THEN 返回 HTTP 404
    """
    user = await UserService.get_by_id(session, user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

    # 获取用户的默认租户
    stmt = select(UserTenant).where(
        UserTenant.user_id == user_id,
        UserTenant.is_default == True
    )
    result = await session.execute(stmt)
    user_tenant = result.scalar_one_or_none()
    tenant_id = user_tenant.tenant_id if user_tenant else None

    return ApiResponse.success(data=build_user_info(user, tenant_id).model_dump())


@router.post("/users/batch")
async def get_users_batch(
    data: BatchUsersRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    批量获取用户

    场景：批量获取用户
    WHEN 请求 POST /iam/inner/v1/users/batch
    WITH 请求体 {"user_ids": ["id1", "id2"]}
    THEN 返回多个用户的信息列表
    """
    if not data.user_ids:
        return ApiResponse.success(data=[])

    users = await UserService.get_by_ids(session, data.user_ids)

    # 获取用户的默认租户
    user_tenant_map = {}
    stmt = select(UserTenant).where(
        UserTenant.user_id.in_(data.user_ids),
        UserTenant.is_default == True
    )
    result = await session.execute(stmt)
    for ut in result.scalars().all():
        user_tenant_map[ut.user_id] = ut.tenant_id

    return ApiResponse.success(data=[build_user_info(u, user_tenant_map.get(u.id)).model_dump() for u in users if u])


@router.get("/users/{user_id}/organizations")
async def get_user_organizations(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取用户组织

    场景：获取用户组织
    WHEN 请求 GET /iam/inner/v1/users/{user_id}/organizations
    THEN 返回用户所属的组织列表
    """
    stmt = select(UserOrganization).where(UserOrganization.user_id == user_id)
    result = await session.execute(stmt)
    user_organizations = result.scalars().all()

    organization_ids = [uo.organization_id for uo in user_organizations]

    if not organization_ids:
        return ApiResponse.success(
            data=UserOrganizationResponse(
                user_id=user_id,
                organizations=[],
            ).model_dump()
        )

    # 获取组织详情
    organizations = await OrganizationService.get_by_ids(session, organization_ids)

    org_list = [
        OrganizationInfoInnerResponse(
            id=d.id,
            name=d.name,
            parent_id=d.parent_id,
            tree_level=d.tree_level,
            tree_path=d.tree_path,
        )
        for d in organizations if d
    ]

    return ApiResponse.success(
        data=UserOrganizationResponse(
            user_id=user_id,
            organizations=org_list,
        ).model_dump()
    )


@router.get("/users/{user_id}/tenants")
async def get_user_tenants(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取用户租户列表

    场景：获取用户租户列表
    WHEN 请求 GET /iam/inner/v1/users/{user_id}/tenants
    THEN 返回用户所属的租户列表，包含 role 和 is_default
    """
    tenants = await UserService.get_user_tenants_detail(session, user_id)

    return ApiResponse.success(
        data=UserTenantsResponse(
            user_id=user_id,
            tenants=[
                UserTenantInfo(
                    tenant_id=t["tenant_id"],
                    role=t["role"],
                    is_default=t["is_default"],
                )
                for t in tenants
            ],
        ).model_dump()
    )


@router.get("/tenants/{tenant_id}/users")
async def get_tenant_users(
    tenant_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取租户下的用户 ID 列表

    场景：获取租户用户列表
    WHEN 请求 GET /iam/inner/v1/tenants/{tenant_id}/users
    THEN 返回该租户下所有用户的 ID 列表
    """
    user_ids = await UserService.get_user_ids_by_tenant_id(session, tenant_id)

    return ApiResponse.success(
        data=TenantUsersResponse(
            tenant_id=tenant_id,
            user_ids=user_ids,
        ).model_dump()
    )
