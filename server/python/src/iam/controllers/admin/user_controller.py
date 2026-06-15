"""
用户控制器 - 管理员端

提供用户管理、角色分配、部门分配等管理员接口。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy import select

from iam.models import UserDepartment
from iam.schemas.user import (
    AdminPasswordResetRequest,
    AdminPasswordResetVo,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    UserDepartmentAssignRequest,
    UserListVo,
    UserRoleAssignRequest,
    UserStatusUpdateRequest,
    UserVo,
)
from iam.services import department_service, user_service
from iam.services.role_service import user_role_service as user_roles_service
from framework.database.core.engine import async_session
from framework.tenant.context import get_tenant_id

router = APIRouter()


@router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: str | None = None,
) -> ORJSONResponse:
    """
    获取用户列表

    支持分页、关键词搜索、状态过滤。
    """
    tenant_id = get_tenant_id()

    users, total = await user_service.list_users(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
    )
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": UserListVo(
                total=total,
                items=[UserVo.model_validate(u) for u in users],
            ).model_dump(),
        }
    )


@router.post("/users")
async def create_user(data: AdminUserCreateRequest) -> ORJSONResponse:
    """
    管理员创建用户

    创建新用户账号。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")

    try:
        user = await user_service.create_user(
            username=data.username,
            password=data.password,
            tenant_id=tenant_id,
            email=data.email,
            phone=data.phone,
            nickname=data.nickname,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "创建成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}")
async def get_user(user_id: str) -> ORJSONResponse:
    """
    获取用户详情

    返回指定用户的详细信息。
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": UserVo.model_validate(user).model_dump(),
        }
    )


@router.put("/users/{user_id}")
async def update_user(user_id: str, data: AdminUserUpdateRequest) -> ORJSONResponse:
    """
    更新用户信息

    管理员更新用户信息。
    """
    try:
        user = await user_service.update_user(
            user_id=user_id,
            nickname=data.nickname,
            avatar=data.avatar,
            email=data.email,
            phone=data.phone,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "更新成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(user_id: str) -> ORJSONResponse:
    """
    删除用户

    软删除用户（设置状态为 inactive）。
    """
    try:
        await user_service.soft_delete(user_id)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "删除成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/enable")
async def enable_user(user_id: str) -> ORJSONResponse:
    """
    激活用户

    将用户状态设置为 active。
    """
    try:
        user = await user_service.set_status(user_id, "active")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "激活成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/disable")
async def disable_user(user_id: str) -> ORJSONResponse:
    """
    停用用户

    将用户状态设置为 inactive。
    """
    try:
        user = await user_service.set_status(user_id, "inactive")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "停用成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/lock")
async def lock_user(user_id: str) -> ORJSONResponse:
    """
    锁定用户

    将用户状态设置为 locked。
    """
    try:
        user = await user_service.set_status(user_id, "locked")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "锁定成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str, data: UserStatusUpdateRequest
) -> ORJSONResponse:
    """
    更新用户状态

    更新用户状态 (active/inactive/locked)。
    """
    try:
        user = await user_service.set_status(user_id, data.status)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "状态更新成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    data: AdminPasswordResetRequest | None = None,
) -> ORJSONResponse:
    """
    重置用户密码

    管理员重置用户密码。如果未提供新密码，则生成随机密码。
    """
    try:
        password = await user_service.admin_reset_password(
            user_id=user_id,
            new_password=data.new_password if data else None,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码重置成功",
                "data": AdminPasswordResetVo(password=password).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/roles")
async def get_user_roles(user_id: str) -> ORJSONResponse:
    """
    获取用户角色列表

    返回用户已分配的角色。
    """
    roles = await user_roles_service.get_user_roles(user_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [
                {
                    "id": r.id,
                    "code": r.code,
                    "name": r.name,
                    "description": r.description,
                }
                for r in roles
            ],
        }
    )


@router.post("/users/{user_id}/roles")
async def assign_user_roles(
    user_id: str, data: UserRoleAssignRequest
) -> ORJSONResponse:
    """
    分配用户角色

    为用户分配角色（覆盖式分配）。
    """
    try:
        await user_roles_service.assign_roles(user_id, data.role_ids)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "角色分配成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/departments")
async def get_user_departments(user_id: str) -> ORJSONResponse:
    """
    获取用户部门列表

    返回用户所属的部门。
    """
    departments = await user_service.get_user_departments(user_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": departments,
        }
    )


@router.post("/users/{user_id}/departments")
async def assign_user_departments(
    user_id: str,
    data: UserDepartmentAssignRequest,
) -> ORJSONResponse:
    """
    分配用户部门

    为用户分配部门（覆盖式分配）。
    """
    try:
        async with async_session() as session:
            stmt = select(UserDepartment).where(UserDepartment.user_id == user_id)
            result = await session.execute(stmt)
            for ud in result.scalars().all():
                await session.delete(ud)
            await session.commit()

        for dept_id in data.department_ids:
            try:
                await department_service.add_user(
                    department_id=dept_id,
                    user_id=user_id,
                )
            except ValueError:
                pass

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "部门分配成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
