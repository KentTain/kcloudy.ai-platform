"""管理端标签控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.tag import TagCreate, TagPaginatedQuery, TagResponse, TagGroupResponse
from document.services.tag_service import tag_service

router = APIRouter()


@router.get("/tags")
async def list_tags(
    query: TagPaginatedQuery = Depends(),
    tenant_id: str = "",
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """管理端查看标签列表"""
    items, total = await tag_service.list_tags(
        session,
        tenant_id=tenant_id,
        group_id=query.group_id,
        keyword=query.keyword,
        page=query.page,
        page_size=query.page_size,
    )
    return ApiResponse.paginated(
        data=[TagResponse.model_validate(t).model_dump() for t in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.post("/tags")
async def create_tag(
    data: TagCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建标签"""
    try:
        tag = await tag_service.create(
            session,
            name=data.name,
            group_id=data.group_id,
            color=data.color,
            description=data.description,
            persona_id=data.persona_id,
        )
        await session.commit()
        return ApiResponse.success(data=TagResponse.model_validate(tag).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除标签"""
    try:
        await tag_service.delete(session, tag_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tag-groups")
async def list_tag_groups(
    tenant_id: str = "",
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看标签分组列表"""
    groups = await tag_service.list_groups(session, tenant_id=tenant_id)
    return ApiResponse.success(data=[TagGroupResponse.model_validate(g).model_dump() for g in groups])
