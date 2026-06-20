"""
IAM 模块内部接口控制器 - 组织

提供模块间内部调用接口，不对外暴露。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.models import Organization
from iam.services.organization_service import OrganizationService

router = APIRouter()


class OrganizationInfoResponse(BaseModel):
    """组织信息响应"""
    id: str = Field(..., description="组织ID")
    name: str = Field(..., description="组织名称")
    parent_id: str | None = Field(None, description="父组织ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")


class OrganizationTreeInnerResponse(BaseModel):
    """组织树响应"""
    id: str = Field(..., description="组织ID")
    name: str = Field(..., description="组织名称")
    parent_id: str | None = Field(None, description="父组织ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")
    children: list["OrganizationTreeInnerResponse"] = Field(default_factory=list, description="子组织")


def build_organization_info(org: Organization) -> OrganizationInfoResponse:
    """构建组织信息响应"""
    return OrganizationInfoResponse(
        id=org.id,
        name=org.name,
        parent_id=org.parent_id,
        tree_level=org.tree_level,
        tree_path=org.tree_path,
    )


def build_organization_tree(organizations: list[Organization]) -> list[OrganizationTreeInnerResponse]:
    """构建组织树"""
    # 按父ID分组
    children_map: dict[str | None, list[Organization]] = {}
    for org in organizations:
        parent_id = org.parent_id or None
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(org)

    def build_node(org: Organization) -> OrganizationTreeInnerResponse:
        children = children_map.get(org.id, [])
        return OrganizationTreeInnerResponse(
            id=org.id,
            name=org.name,
            parent_id=org.parent_id,
            tree_level=org.tree_level,
            tree_path=org.tree_path,
            children=[build_node(c) for c in children],
        )

    # 找到根节点
    roots = children_map.get(None, [])
    return [build_node(r) for r in roots]


@router.get("/organizations/tree")
async def get_organization_tree(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取组织树

    场景：获取组织树
    WHEN 请求 GET /inner/v1/organizations/tree
    THEN 返回完整的组织树结构
    """
    stmt = select(Organization).order_by(Organization.tree_sort)
    result = await session.execute(stmt)
    organizations = list(result.scalars().all())

    tree = build_organization_tree(organizations)

    return ApiResponse.success(data=[t.model_dump() for t in tree])


@router.get("/organizations/{organization_id}")
async def get_organization(
    organization_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取单个组织

    场景：获取单个组织
    WHEN 请求 GET /inner/v1/organizations/{organization_id}
    THEN 返回指定组织的详细信息

    场景：组织不存在
    WHEN 请求 GET /inner/v1/organizations/nonexistent
    THEN 返回 HTTP 404
    """
    org = await OrganizationService.get_by_id(session, organization_id)

    if not org:
        raise HTTPException(status_code=404, detail=f"组织 {organization_id} 不存在")

    return ApiResponse.success(data=build_organization_info(org).model_dump())
