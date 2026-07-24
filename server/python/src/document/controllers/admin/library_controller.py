"""管理端文档库控制器"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.library import LibraryPaginatedQuery, LibraryResponse
from document.services.library_service import library_service

router = APIRouter()


@router.get("/libraries")
async def list_libraries(
    query: LibraryPaginatedQuery = Depends(),
    tenant_id: str = "",
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """管理端查看所有租户的文档库"""
    items, total = await library_service.list_libraries(
        session,
        tenant_id=tenant_id or None,
        page=query.page,
        page_size=query.page_size,
        keyword=query.keyword,
        library_type=query.library_type,
    )
    return ApiResponse.paginated(
        data=[LibraryResponse.model_validate(lib).model_dump() for lib in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
