"""
IAM 模块内部接口控制器

提供模块间内部调用接口，不对外暴露。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from typing import Any

from iam.models import User, UserTenant
from iam.services.user_service import UserService
from iam.services.department_service import DepartmentService
from framework.database.core.engine import async_session
from sqlalchemy import select

router = APIRouter()


def Success(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


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


class DepartmentInfoResponse(BaseModel):
    """部门信息响应"""
    id: str = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    parent_id: str | None = Field(None, description="父部门ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")


class UserDepartmentResponse(BaseModel):
    """用户部门响应"""
    user_id: str = Field(..., description="用户ID")
    departments: list[DepartmentInfoResponse] = Field(default_factory=list, description="部门列表")


class DepartmentTreeResponse(BaseModel):
    """部门树响应"""
    id: str = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    parent_id: str | None = Field(None, description="父部门ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")
    children: list["DepartmentTreeResponse"] = Field(default_factory=list, description="子部门")


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
async def get_user(user_id: str) -> ORJSONResponse:
    """
    获取单个用户

    场景：获取单个用户
    WHEN 请求 GET /inner/v1/users/{user_id}
    THEN 返回指定用户的详细信息
    AND 不依赖 Token 认证
    AND user_id 由调用方显式传入

    场景：用户不存在
    WHEN 请求 GET /inner/v1/users/nonexistent
    THEN 返回 HTTP 404
    """
    user = await UserService.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

    # 获取用户的默认租户
    tenant_id = None
    async with async_session() as session:
        stmt = select(UserTenant).where(
            UserTenant.user_id == user_id,
            UserTenant.is_default == True
        )
        result = await session.execute(stmt)
        user_tenant = result.scalar_one_or_none()
        if user_tenant:
            tenant_id = user_tenant.tenant_id

    return ORJSONResponse(
        content=Success(build_user_info(user, tenant_id).model_dump())
    )


@router.post("/users/batch")
async def get_users_batch(data: BatchUsersRequest) -> ORJSONResponse:
    """
    批量获取用户

    场景：批量获取用户
    WHEN 请求 POST /inner/v1/users/batch
    WITH 请求体 {"user_ids": ["id1", "id2"]}
    THEN 返回多个用户的信息列表
    """
    if not data.user_ids:
        return ORJSONResponse(content=Success([]))

    users = await UserService.get_by_ids(data.user_ids)

    # 获取用户的默认租户
    user_tenant_map = {}
    async with async_session() as session:
        stmt = select(UserTenant).where(
            UserTenant.user_id.in_(data.user_ids),
            UserTenant.is_default == True
        )
        result = await session.execute(stmt)
        for ut in result.scalars().all():
            user_tenant_map[ut.user_id] = ut.tenant_id

    return ORJSONResponse(
        content=Success([build_user_info(u, user_tenant_map.get(u.id)).model_dump() for u in users if u])
    )


@router.get("/users/{user_id}/departments")
async def get_user_departments(user_id: str) -> ORJSONResponse:
    """
    获取用户部门

    场景：获取用户部门
    WHEN 请求 GET /inner/v1/users/{user_id}/departments
    THEN 返回用户所属的部门列表
    """
    from iam.models import UserDepartment

    async with async_session() as session:
        stmt = select(UserDepartment).where(UserDepartment.user_id == user_id)
        result = await session.execute(stmt)
        user_departments = result.scalars().all()

        department_ids = [ud.department_id for ud in user_departments]

        if not department_ids:
            return ORJSONResponse(
                content=Success(
                    UserDepartmentResponse(
                        user_id=user_id,
                        departments=[],
                    ).model_dump()
                )
            )

        # 获取部门详情
        departments = await DepartmentService.get_by_ids(department_ids)

        dept_list = [
            DepartmentInfoResponse(
                id=d.id,
                name=d.name,
                parent_id=d.parent_id,
                tree_level=d.tree_level,
                tree_path=d.tree_path,
            )
            for d in departments if d
        ]

        return ORJSONResponse(
            content=Success(
                UserDepartmentResponse(
                    user_id=user_id,
                    departments=dept_list,
                ).model_dump()
            )
        )


@router.get("/users/{user_id}/tenants")
async def get_user_tenants(user_id: str) -> ORJSONResponse:
    """
    获取用户租户列表

    场景：获取用户租户列表
    WHEN 请求 GET /inner/v1/users/{user_id}/tenants
    THEN 返回用户所属的租户列表，包含 role 和 is_default
    """
    tenants = await UserService.get_user_tenants_detail(user_id)

    return ORJSONResponse(
        content=Success(
            UserTenantsResponse(
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
    )


@router.get("/tenants/{tenant_id}/users")
async def get_tenant_users(tenant_id: str) -> ORJSONResponse:
    """
    获取租户下的用户 ID 列表

    场景：获取租户用户列表
    WHEN 请求 GET /inner/v1/tenants/{tenant_id}/users
    THEN 返回该租户下所有用户的 ID 列表
    """
    user_ids = await UserService.get_user_ids_by_tenant_id(tenant_id)

    return ORJSONResponse(
        content=Success(
            TenantUsersResponse(
                tenant_id=tenant_id,
                user_ids=user_ids,
            ).model_dump()
        )
    )
