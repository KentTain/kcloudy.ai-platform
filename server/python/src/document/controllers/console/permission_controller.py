"""用户端权限配置控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.permission import (
    LibraryRoleCreate,
    LibraryRoleMemberAdd,
    ResourceAclCreate,
    InheritanceUpdate,
    LibraryRoleResponse,
    LibraryRoleMemberResponse,
    ResourceAclResponse,
)
from document.services.permission_config_service import permission_config_service

router = APIRouter()


@router.get("/libraries/{library_id}/roles")
async def list_roles(
    library_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看文档库权限组列表"""
    roles = await permission_config_service.list_roles(session, library_id=library_id)
    return ApiResponse.success(data=[LibraryRoleResponse.model_validate(r).model_dump() for r in roles])


@router.post("/libraries/{library_id}/roles")
async def create_role(
    library_id: str,
    data: LibraryRoleCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建权限组"""
    try:
        role = await permission_config_service.create_role(
            session,
            library_id=library_id,
            code=data.code,
            name=data.name,
            description=data.description,
        )
        await session.commit()
        return ApiResponse.success(data=LibraryRoleResponse.model_validate(role).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles/{role_id}/members")
async def list_role_members(
    role_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看权限组成员列表"""
    members = await permission_config_service.list_role_members(session, role_id=role_id)
    return ApiResponse.success(
        data=[LibraryRoleMemberResponse.model_validate(m).model_dump() for m in members]
    )


@router.post("/roles/{role_id}/members")
async def add_role_member(
    role_id: str,
    data: LibraryRoleMemberAdd,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """添加权限组成员"""
    try:
        member = await permission_config_service.add_role_member(
            session,
            library_id=data.library_id,
            role_id=role_id,
            user_id=data.user_id,
        )
        await session.commit()
        return ApiResponse.success(data=LibraryRoleMemberResponse.model_validate(member).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/libraries/{library_id}/resource-acls")
async def list_resource_acls(
    library_id: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看资源 ACL 列表"""
    acls = await permission_config_service.list_resource_acls(
        session,
        library_id=library_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    return ApiResponse.success(data=[ResourceAclResponse.model_validate(a).model_dump() for a in acls])


@router.post("/libraries/{library_id}/resource-acls")
async def create_resource_acl(
    library_id: str,
    data: ResourceAclCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建资源 ACL"""
    try:
        acl = await permission_config_service.create_resource_acl(
            session,
            library_id=library_id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            subject_id=data.subject_id,
            subject_type=data.subject_type,
            action=data.action,
            effect=data.effect,
            priority=data.priority,
        )
        await session.commit()
        return ApiResponse.success(data=ResourceAclResponse.model_validate(acl).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/libraries/{library_id}/inheritance")
async def update_inheritance(
    library_id: str,
    data: InheritanceUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新权限继承"""
    try:
        await permission_config_service.update_inheritance(
            session,
            library_id=library_id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            inherit_enabled=data.inherit_enabled,
        )
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
