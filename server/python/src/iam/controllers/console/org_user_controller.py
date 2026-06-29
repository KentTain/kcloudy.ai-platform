"""
组织人员相关 API 控制器

提供人员选择组件所需的组织人员树、用户搜索、组织搜索等接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.dependencies import get_current_user_id, get_current_tenant_id
from iam.schemas.org_user import (
    OrgUserTreeResponse,
    OrgUsersQuery,
    OrgSearchQuery,
    OrganizationBatchBody,
    OrganizationBatchResponse,
    UserBatchBody,
    UserBatchResponse,
    UserSearchQuery,
)
from iam.services.organization_service import organization_service
from iam.services.user_service import user_service

router = APIRouter()


# ==============================================================================
# 组织人员树
# ==============================================================================


@router.get("/org-users/tree")
async def get_org_user_tree(
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ORJSONResponse:
    """
    获取组织人员树

    返回当前租户的组织树，每个组织节点包含直属人员列表和统计信息。

    场景：人员选择组件加载
    WHEN 人员选择组件初始化
    THEN 系统返回组织人员树，用于展示组织结构和人员分布

    Returns:
        ORJSONResponse: 组织人员树响应
    """
    tree = await organization_service.get_org_user_tree(session, tenant_id)

    response = OrgUserTreeResponse(items=tree)
    return ApiResponse.success(data=response.model_dump())


# ==============================================================================
# 组织用户
# ==============================================================================


@router.get("/org-users/{org_id}/users")
async def get_org_users(
    org_id: str,
    include_children: bool = False,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    获取组织下的人员

    返回指定组织的直属人员列表，可选包含下级组织人员。

    场景：查看组织人员
    WHEN 用户点击组织节点
    THEN 系统返回该组织的直属人员列表

    场景：查看组织及下级人员
    WHEN 用户勾选"包含下级组织"
    THEN 系统返回该组织及其所有子组织的人员列表

    Args:
        org_id: 组织 ID
        include_children: 是否包含下级组织用户，默认 False

    Returns:
        ORJSONResponse: 用户列表
    """
    users = await organization_service.get_org_users(
        session, org_id, include_children=include_children
    )

    return ApiResponse.success(data=[user.model_dump() for user in users])


# ==============================================================================
# 用户搜索
# ==============================================================================


@router.get("/users/search")
async def search_users(
    query: UserSearchQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ORJSONResponse:
    """
    搜索用户

    根据关键词搜索用户，支持按组织过滤。

    场景：搜索用户
    WHEN 用户在人员选择器中输入关键词
    THEN 系统返回匹配的用户列表

    场景：搜索组织内用户
    WHEN 用户指定组织并输入关键词
    THEN 系统返回该组织（及其下级）中匹配的用户列表

    Args:
        query: 用户搜索查询参数

    Returns:
        ORJSONResponse: 用户分页列表
    """
    result = await user_service.search_users(
        session,
        tenant_id=tenant_id,
        keyword=query.keyword,
        org_id=query.org_id,
        include_children=query.include_children,
        page=query.page,
        page_size=query.page_size,
    )

    return ApiResponse.paginated(
        data=[user.model_dump() for user in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post("/users/batch")
async def get_users_batch(
    body: UserBatchBody,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    批量获取用户

    根据用户 ID 列表批量获取用户信息。

    场景：回显已选用户
    WHEN 人员选择组件需要显示已选用户信息
    THEN 系统根据用户 ID 列表返回用户详细信息

    Args:
        body: 批量获取用户请求体

    Returns:
        ORJSONResponse: 用户列表
    """
    users = await user_service.get_users_by_ids(session, body.user_ids)

    response = UserBatchResponse(items=users)
    return ApiResponse.success(data=response.model_dump())


@router.get("/users/{user_id}/avatar")
async def get_user_avatar(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    获取用户头像

    返回指定用户的头像 URL。

    场景：加载用户头像
    WHEN 前端需要显示用户头像
    THEN 系统返回用户头像 URL

    Args:
        user_id: 用户 ID

    Returns:
        ORJSONResponse: 头像 URL 或 null
    """
    avatar_url = await user_service.get_user_avatar_url(session, user_id)

    return ApiResponse.success(data={"avatar": avatar_url})


# ==============================================================================
# 组织搜索
# ==============================================================================


@router.get("/organizations/search")
async def search_organizations(
    query: OrgSearchQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ORJSONResponse:
    """
    搜索组织

    根据关键词搜索组织，支持按父组织过滤。

    场景：搜索组织
    WHEN 用户在组织选择器中输入关键词
    THEN 系统返回匹配的组织列表

    场景：搜索子组织
    WHEN 用户指定父组织并输入关键词
    THEN 系统返回该父组织下匹配的子组织列表

    Args:
        query: 组织搜索查询参数

    Returns:
        ORJSONResponse: 组织分页列表
    """
    result = await organization_service.search_organizations(
        session,
        tenant_id=tenant_id,
        keyword=query.keyword,
        parent_id=query.parent_id,
        page=query.page,
        page_size=query.page_size,
    )

    return ApiResponse.paginated(
        data=[org.model_dump() for org in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post("/organizations/batch")
async def get_organizations_batch(
    body: OrganizationBatchBody,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """
    批量获取组织

    根据组织 ID 列表批量获取组织信息。

    场景：回显已选组织
    WHEN 组织选择组件需要显示已选组织信息
    THEN 系统根据组织 ID 列表返回组织详细信息

    Args:
        body: 批量获取组织请求体

    Returns:
        ORJSONResponse: 组织列表
    """
    orgs = await organization_service.get_organizations_by_ids(session, body.org_ids)

    response = OrganizationBatchResponse(items=orgs)
    return ApiResponse.success(data=response.model_dump())
