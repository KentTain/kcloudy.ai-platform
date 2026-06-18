"""
角色控制器

提供角色管理接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse

from iam.schemas.role import (
    RoleCreate,
    RolePermissionRequest,
    RoleUpdate,
    RoleResponse,
    RolePaginatedListResponse,
    RolePaginatedQuery,
    RoleOptionResponse,
    RoleMemberAssignRequest,
    RoleMenuAssignRequest,
    RoleMemberResponse,
)
from iam.services import permission_service, role_service
from iam.services.role_service import role_member_service, user_role_service

router = APIRouter()


@router.get("/roles")
async def list_roles(
    query: RolePaginatedQuery = Depends(),
    tenant_id: str | None = None,
) -> ORJSONResponse:
    """获取角色列表"""
    roles, total = await role_service.list_roles(
        tenant_id=tenant_id,
        page=query.page,
        page_size=query.page_size,
    )
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": RolePaginatedListResponse(
                total=total,
                page=query.page,
                page_size=query.page_size,
                items=[RoleResponse.model_validate(r) for r in roles],
            ).model_dump(),
        }
    )


@router.post("/roles")
async def create_role(data: RoleCreate) -> ORJSONResponse:
    """创建角色"""
    try:
        role = await role_service.create(
            code=data.code,
            name=data.name,
            description=data.description,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "创建成功",
                "data": RoleResponse.model_validate(role).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles/options")
async def get_role_options() -> ORJSONResponse:
    """获取角色选项列表（不分页，供下拉选择用）"""
    roles = await user_role_service.get_role_options()
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [
                RoleOptionResponse.model_validate(r).model_dump()
                for r in roles
            ],
        }
    )


@router.get("/roles/{role_id}")
async def get_role(role_id: str) -> ORJSONResponse:
    """获取角色详情"""
    role = await role_service.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": RoleResponse.model_validate(role).model_dump(),
        }
    )


@router.put("/roles/{role_id}")
async def update_role(role_id: str, data: RoleUpdate) -> ORJSONResponse:
    """更新角色"""
    try:
        role = await role_service.update(
            role_id=role_id,
            name=data.name,
            description=data.description,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "更新成功",
                "data": RoleResponse.model_validate(role).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str) -> ORJSONResponse:
    """删除角色"""
    try:
        await role_service.delete(role_id)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "删除成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(role_id: str) -> ORJSONResponse:
    """获取角色的权限列表"""
    permissions = await role_service.get_role_permissions(role_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [
                {
                    "id": p.id,
                    "code": p.code,
                    "name": p.name,
                    "resource": p.resource,
                    "action": p.action,
                }
                for p in permissions
            ],
        }
    )


@router.post("/roles/{role_id}/permissions")
async def assign_permissions(role_id: str, data: RolePermissionRequest) -> ORJSONResponse:
    """为角色分配权限"""
    await role_service.assign_permissions(role_id, data.permission_ids)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "分配成功",
            "data": None,
        }
    )


@router.get("/roles/{role_id}/members")
async def get_role_members(role_id: str) -> ORJSONResponse:
    """获取角色成员列表"""
    members = await role_member_service.get_role_members(role_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": members,
        }
    )


@router.post("/roles/{role_id}/members")
async def add_role_members(role_id: str, data: RoleMemberAssignRequest) -> ORJSONResponse:
    """为角色添加成员"""
    try:
        added = await role_member_service.add_role_members(role_id, data.user_ids)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": f"成功添加 {added} 个成员",
                "data": {"added": added},
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/roles/{role_id}/members/{user_id}")
async def remove_role_member(role_id: str, user_id: str) -> ORJSONResponse:
    """移除角色成员"""
    removed = await role_member_service.remove_role_member(role_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="该用户不是此角色成员")
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "移除成功",
            "data": None,
        }
    )


@router.get("/roles/{role_id}/menus")
async def get_role_menus(role_id: str) -> ORJSONResponse:
    """获取角色已分配的菜单 ID 列表"""
    menu_ids = await role_member_service.get_role_menus(role_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": menu_ids,
        }
    )


@router.post("/roles/{role_id}/menus")
async def assign_role_menus(role_id: str, data: RoleMenuAssignRequest) -> ORJSONResponse:
    """为角色分配菜单"""
    try:
        await role_member_service.assign_role_menus(role_id, data.menu_ids)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "分配成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
