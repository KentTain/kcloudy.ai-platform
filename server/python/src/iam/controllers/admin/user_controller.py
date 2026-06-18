"""
用户控制器 - 管理员端

提供用户管理、角色分配、部门分配等管理员接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import UserDepartment
from iam.schemas.user import (
    AdminPasswordResetRequest,
    AdminPasswordResetResponse,
    AdminUserCreate,
    AdminUserUpdate,
    UserDepartmentAssignRequest,
    UserPaginatedListResponse,
    UserPaginatedQuery,
    UserRoleAssignRequest,
    UserStatusUpdateRequest,
    UserResponse,
)
from iam.services import department_service, user_service
from iam.services.role_service import user_role_service as user_roles_service
from framework.database.dependencies import get_db_session
from framework.tenant.context import get_tenant_id

router = APIRouter()


@router.get("/users")
async def list_users(
    query: UserPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取用户列表

    支持分页、关键词搜索、状态过滤、部门筛选。
    """
    tenant_id = get_tenant_id()

    users, total = await user_service.list_users(
        session,
        tenant_id=tenant_id,
        page=query.page,
        page_size=query.page_size,
        keyword=query.keyword,
        status=query.status,
        dept_id=query.dept_id,
        include_children=query.include_children,
    )
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": UserPaginatedListResponse(
                total=total,
                page=query.page,
                page_size=query.page_size,
                items=[UserResponse.model_validate(u) for u in users],
            ).model_dump(),
        }
    )


@router.get("/users/stats")
async def get_user_stats() -> ORJSONResponse:
    """
    获取用户统计

    返回用户总数、启用数、停用数、多角色用户数。
    """
    from iam.schemas.user import UserStatsResponse

    tenant_id = get_tenant_id()
    stats = await user_service.get_user_stats(tenant_id)

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": UserStatsResponse(**stats).model_dump(),
        }
    )


@router.post("/users")
async def create_user(
    data: AdminUserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    管理员创建用户

    创建新用户账号。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")

    try:
        user = await user_service.create_user(
            session,
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
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取用户详情

    返回指定用户的详细信息。
    """
    user = await user_service.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": UserResponse.model_validate(user).model_dump(),
        }
    )


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: AdminUserUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新用户信息

    管理员更新用户信息。
    """
    try:
        user = await user_service.update_user(
            session,
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
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除用户

    软删除用户（设置状态为 inactive）。
    """
    try:
        await user_service.soft_delete(session, user_id)
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
async def enable_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    激活用户

    将用户状态设置为 active。
    """
    try:
        user = await user_service.set_status(session, user_id, "active")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "激活成功",
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    停用用户

    将用户状态设置为 inactive。
    """
    try:
        user = await user_service.set_status(session, user_id, "inactive")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "停用成功",
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    锁定用户

    将用户状态设置为 locked。
    """
    try:
        user = await user_service.set_status(session, user_id, "locked")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "锁定成功",
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    data: UserStatusUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新用户状态

    更新用户状态 (active/inactive/locked)。
    """
    try:
        user = await user_service.set_status(session, user_id, data.status)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "状态更新成功",
                "data": UserResponse.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    data: AdminPasswordResetRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    重置用户密码

    管理员重置用户密码。如果未提供新密码，则生成随机密码。
    """
    try:
        password = await user_service.admin_reset_password(
            session,
            user_id=user_id,
            new_password=data.new_password if data else None,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码重置成功",
                "data": AdminPasswordResetResponse(password=password).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取用户角色列表

    返回用户已分配的角色。
    """
    from iam.schemas.user import UserRoleItem

    roles = await user_roles_service.get_user_roles(session, user_id)
    # 使用 Schema 转换方法，但保持原始数组格式
    items = [UserRoleItem.from_role(r).model_dump() for r in roles]
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": items,
        }
    )


@router.post("/users/{user_id}/roles")
async def assign_user_roles(
    user_id: str,
    data: UserRoleAssignRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    分配用户角色

    为用户分配角色（覆盖式分配）。
    """
    try:
        await user_roles_service.assign_roles(session, user_id, data.role_ids)
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
async def get_user_departments(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取用户部门列表

    返回用户所属的部门。
    """
    departments = await user_service.get_user_departments(session, user_id)
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
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    分配用户部门

    为用户分配部门（覆盖式分配）。
    """
    try:
        stmt = select(UserDepartment).where(UserDepartment.user_id == user_id)
        result = await session.execute(stmt)
        for ud in result.scalars().all():
            await session.delete(ud)
        await session.flush()

        for dept_id in data.department_ids:
            try:
                await department_service.add_user(
                    session,
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
