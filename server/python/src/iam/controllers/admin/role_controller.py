"""
角色控制器

提供角色管理接口。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from iam.schemas.role import (
    RoleCreateRequest,
    RolePermissionRequest,
    RoleUpdateRequest,
    RoleVo,
)
from iam.services import permission_service, role_service

router = APIRouter()


@router.get("/roles")
async def list_roles(tenant_id: str | None = None, page: int = 1, page_size: int = 20) -> ORJSONResponse:
    """获取角色列表"""
    roles, total = await role_service.list_roles(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
    )
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [RoleVo.model_validate(r).model_dump() for r in roles],
            "total": total,
        }
    )


@router.post("/roles")
async def create_role(data: RoleCreateRequest) -> ORJSONResponse:
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
                "data": RoleVo.model_validate(role).model_dump(),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
            "data": RoleVo.model_validate(role).model_dump(),
        }
    )


@router.put("/roles/{role_id}")
async def update_role(role_id: str, data: RoleUpdateRequest) -> ORJSONResponse:
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
                "data": RoleVo.model_validate(role).model_dump(),
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
