"""用户端回收站控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.recycle import RecyclePaginatedQuery, RecycleItemResponse
from document.services.recycle_service import recycle_service

router = APIRouter()


@router.get("/libraries/{library_id}/recycle")
async def list_recycle_items(
    library_id: str,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看回收站列表"""
    items, total = await recycle_service.list_items(
        session,
        library_id=library_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.paginated(
        data=[RecycleItemResponse.model_validate(item).model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/recycle/{item_id}/restore")
async def restore_item(
    item_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """恢复回收站项目"""
    try:
        await recycle_service.restore(session, item_id=item_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/recycle/{item_id}")
async def purge_item(
    item_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """永久删除回收站项目"""
    try:
        await recycle_service.purge(session, item_id=item_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/libraries/{library_id}/recycle")
async def clear_recycle(
    library_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """清空回收站"""
    count = await recycle_service.clear(session, library_id=library_id)
    await session.commit()
    return ApiResponse.success(data={"purged_count": count})
