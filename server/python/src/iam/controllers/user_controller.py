"""
用户控制器

提供用户注册、信息管理、密码管理等接口。
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import select

from iam.dependencies import get_current_user_id, get_optional_user_id
from iam.models import UserDepartment
from iam.schemas.user import (
    AdminPasswordResetRequest,
    AdminPasswordResetVo,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    PasswordChangeRequest,
    PasswordResetCodeRequest,
    PasswordResetRequest,
    UserDepartmentAssignRequest,
    UserListVo,
    UserRoleAssignRequest,
    UserRegisterRequest,
    UserStatusUpdateRequest,
    UserUpdateRequest,
    UserVo,
)
from iam.services import department_service, user_role_service, user_service
from iam.services.role_service import user_role_service as user_roles_service
from framework.database.core.engine import async_session
from framework.tenant.context import get_tenant_id

router = APIRouter()


# ==================== 用户端接口 ====================


@router.post("/register")
async def register(data: UserRegisterRequest) -> ORJSONResponse:
    """
    用户注册

    创建新用户账号并自动登录。
    """
    from iam.services import auth_service

    # 从上下文获取租户 ID
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")

    try:
        user = await user_service.register(
            username=data.username,
            password=data.password,
            tenant_id=tenant_id,
            email=data.email,
            phone=data.phone,
        )

        # 自动登录，生成 Token
        login_result = await auth_service.login(
            account=data.username,
            password=data.password,
        )

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "注册成功",
                "data": {
                    "user": UserVo.model_validate(user).model_dump(),
                    "access_token": login_result.access_token,
                    "refresh_token": login_result.refresh_token,
                    "expires_in": login_result.expires_in,
                },
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)) -> ORJSONResponse:
    """
    获取当前用户信息

    返回当前登录用户的详细信息。
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


@router.put("/me")
async def update_current_user(
    data: UserUpdateRequest,
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    修改当前用户信息

    更新昵称、头像、邮箱、手机号等。
    """
    try:
        user = await user_service.update_profile(
            user_id=user_id,
            nickname=data.nickname,
            avatar=data.avatar,
            email=data.email,
            phone=data.phone,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "修改成功",
                "data": UserVo.model_validate(user).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/password")
async def change_password(
    data: PasswordChangeRequest,
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    修改密码

    验证原密码后设置新密码。
    """
    try:
        await user_service.change_password(
            user_id=user_id,
            old_password=data.old_password,
            new_password=data.new_password,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码修改成功，请重新登录",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/password/reset-code")
async def send_reset_code(data: PasswordResetCodeRequest) -> ORJSONResponse:
    """
    发送密码重置验证码

    向邮箱或手机号发送 6 位验证码。
    """
    # TODO: 实现验证码发送
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "验证码已发送",
            "data": None,
        }
    )


@router.post("/password/reset")
async def reset_password(data: PasswordResetRequest) -> ORJSONResponse:
    """
    重置密码

    使用验证码重置密码。
    """
    try:
        await user_service.reset_password(
            email=data.email,
            phone=data.phone,
            code=data.code,
            new_password=data.new_password,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "密码重置成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 管理员接口 ====================


@router.get("")
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
    # 从上下文获取租户 ID
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


@router.post("")
async def create_user(data: AdminUserCreateRequest) -> ORJSONResponse:
    """
    管理员创建用户

    创建新用户账号。
    """
    # 从上下文获取租户 ID
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


@router.get("/{user_id}")
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


@router.put("/{user_id}")
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


@router.delete("/{user_id}")
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


@router.post("/{user_id}/enable")
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


@router.post("/{user_id}/disable")
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


@router.post("/{user_id}/lock")
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


@router.put("/{user_id}/status")
async def update_user_status(user_id: str, data: UserStatusUpdateRequest) -> ORJSONResponse:
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


@router.post("/{user_id}/reset-password")
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


@router.get("/{user_id}/roles")
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


@router.post("/{user_id}/roles")
async def assign_user_roles(user_id: str, data: UserRoleAssignRequest) -> ORJSONResponse:
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


@router.get("/{user_id}/departments")
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


@router.post("/{user_id}/departments")
async def assign_user_departments(
    user_id: str,
    data: UserDepartmentAssignRequest,
) -> ORJSONResponse:
    """
    分配用户部门

    为用户分配部门（覆盖式分配）。
    """
    try:
        # 先移除用户所有部门
        async with async_session() as session:
            # 删除现有部门关联
            stmt = select(UserDepartment).where(UserDepartment.user_id == user_id)
            result = await session.execute(stmt)
            for ud in result.scalars().all():
                await session.delete(ud)
            await session.commit()

        # 添加新部门关联
        for dept_id in data.department_ids:
            try:
                await department_service.add_user(
                    department_id=dept_id,
                    user_id=user_id,
                )
            except ValueError:
                # 忽略已存在的错误
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
