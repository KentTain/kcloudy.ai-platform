"""用户端文档库控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_tenant_id
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.library import LibraryCreate, LibraryUpdate, LibraryPaginatedQuery, LibraryResponse
from document.services.library_service import library_service

router = APIRouter()


@router.get("/libraries")
async def list_libraries(
    query: LibraryPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看当前租户的文档库列表"""
    tenant_id = get_tenant_id()
    items, total = await library_service.list_libraries(
        session,
        tenant_id=tenant_id,
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


@router.post("/libraries")
async def create_library(
    data: LibraryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建文档库"""
    try:
        library = await library_service.create(
            session,
            library_type=data.library_type,
            code=data.code,
            name=data.name,
            description=data.description,
            icon=data.icon,
        )
        await session.commit()
        return ApiResponse.success(data=LibraryResponse.model_validate(library).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/libraries/{library_id}")
async def get_library(
    library_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取文档库详情"""
    library = await library_service.get_by_id(session, library_id)
    if not library:
        raise HTTPException(status_code=404, detail="文档库不存在")
    return ApiResponse.success(data=LibraryResponse.model_validate(library).model_dump())


@router.put("/libraries/{library_id}")
async def update_library(
    library_id: str,
    data: LibraryUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新文档库"""
    try:
        library = await library_service.update(
            session,
            library_id=library_id,
            name=data.name,
            description=data.description,
            icon=data.icon,
            enabled=data.enabled,
            allow_submit_to_kb=data.allow_submit_to_kb,
        )
        await session.commit()
        return ApiResponse.success(data=LibraryResponse.model_validate(library).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/libraries/{library_id}")
async def delete_library(
    library_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """软删除文档库"""
    try:
        await library_service.soft_delete(session, library_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
