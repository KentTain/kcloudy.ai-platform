"""
组织控制器

提供组织管理接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from framework.tenant.context import get_tenant_id
from iam.schemas.organization import (
    OrganizationCreate,
    OrganizationDetailResponse,
    OrganizationUpdate,
    OrganizationUserBatchRequest,
    UserOrganizationRequest,
)
from iam.services import organization_service

router = APIRouter()


@router.get("/organizations")
async def list_organizations(
    session: AsyncSession = Depends(get_db_session),
):
    """获取组织列表"""
    from iam.schemas.organization import OrganizationListItem

    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    organizations = await organization_service.list_by_tenant(session, tenant_id)
    # 使用 Schema 转换方法，但保持原始数组格式
    items = [OrganizationListItem.from_organization(o).model_dump() for o in organizations]
    return ApiResponse.success(data=items)


@router.get("/organizations/tree")
async def get_organization_tree(
    session: AsyncSession = Depends(get_db_session),
):
    """获取组织树形结构"""
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    tree = await organization_service.get_tree(session, tenant_id)
    return ApiResponse.success(data=tree)


@router.post("/organizations")
async def create_organization(
    data: OrganizationCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """创建组织"""
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    org = await organization_service.create(
        session,
        tenant_id=tenant_id,
        name=data.name,
        parent_id=data.parent_id,
        code=data.code,
        sort_order=data.sort_order or 0,
        leader_id=data.leader_id,
    )
    return ApiResponse.success(
        data={
            "id": org.id,
            "name": org.name,
            "code": org.code,
        }
    )


@router.put("/organizations/{organization_id}")
async def update_organization(
    organization_id: str,
    data: OrganizationUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新组织"""
    try:
        org = await organization_service.update(
            session,
            organization_id=organization_id,
            name=data.name,
            code=data.code,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
            leader_id=data.leader_id,
            status=data.status,
        )
        return ApiResponse.success(
            data={
                "id": org.id,
                "name": org.name,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/organizations/{organization_id}")
async def delete_organization(
    organization_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """删除组织"""
    try:
        await organization_service.delete(session, organization_id)
        return ApiResponse.success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations/{organization_id}/users")
async def get_organization_users(
    organization_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取组织用户列表"""
    users = await organization_service.get_organization_users(session, organization_id)
    return ApiResponse.success(data=users)


@router.post("/organizations/{organization_id}/users")
async def add_user_to_organization(
    organization_id: str,
    data: UserOrganizationRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """添加用户到组织"""
    try:
        await organization_service.add_user(
            session,
            organization_id=organization_id,
            user_id=data.user_id,
            is_leader=data.is_leader,
        )
        return ApiResponse.success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/organizations/{organization_id}/users/{user_id}")
async def remove_user_from_organization(
    organization_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """从组织移除用户"""
    try:
        removed = await organization_service.remove_user(
            session,
            organization_id=organization_id,
            user_id=user_id,
        )
        if not removed:
            raise HTTPException(status_code=404, detail="用户不在该组织中")
        return ApiResponse.success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations/{organization_id}/detail")
async def get_organization_detail(
    organization_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取组织详情（含统计信息）

    返回组织基本信息 + 直属成员数 + 累计成员数 + 组织路径
    """
    org = await organization_service.get_by_id(session, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    stats = await organization_service.get_organization_stats(session, organization_id)

    return ApiResponse.success(
        data=OrganizationDetailResponse(
            id=org.id,
            name=org.name,
            code=org.code,
            parent_id=org.parent_id,
            sort_order=org.sort_order,
            leader_id=org.leader_id,
            status=org.status,
            created_at=org.created_at,
            path=stats.get("path", ""),
            direct_member_count=stats.get("direct_member_count", 0),
            total_member_count=stats.get("total_member_count", 0),
            children_count=stats.get("children_count", 0),
        ).model_dump()
    )


@router.post("/organizations/{organization_id}/users/batch")
async def batch_add_users_to_organization(
    organization_id: str,
    data: OrganizationUserBatchRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """批量添加用户到组织"""
    try:
        added = await organization_service.batch_add_users(
            session,
            organization_id=organization_id,
            user_ids=data.user_ids,
        )
        return ApiResponse.success(data={"added": added})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/organizations/{organization_id}/users/{user_id}/enable")
async def enable_organization_user(
    organization_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """启用组织成员"""
    from iam.services.user_service import UserService

    try:
        user = await UserService.set_status(session, user_id, "active")
        return ApiResponse.success(data={"user_id": user.id, "status": user.status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/organizations/{organization_id}/users/{user_id}/disable")
async def disable_organization_user(
    organization_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """停用组织成员"""
    from iam.services.user_service import UserService

    try:
        user = await UserService.set_status(session, user_id, "inactive")
        return ApiResponse.success(data={"user_id": user.id, "status": user.status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations/{organization_id}/members")
async def get_organization_members(
    organization_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取组织成员列表（详细版）"""
    users = await organization_service.get_organization_users(session, organization_id)
    return ApiResponse.success(data=users)
