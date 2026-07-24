"""用户端文件夹控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.folder import FolderCreate, FolderRename, FolderMove, FolderResponse
from document.services.folder_service import folder_service

router = APIRouter()


@router.get("/folders")
async def list_folders(
    library_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取文件夹树"""
    tree = await folder_service.list_tree(session, library_id=library_id)
    return ApiResponse.success(data=tree)


@router.post("/folders")
async def create_folder(
    data: FolderCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建文件夹"""
    try:
        folder = await folder_service.create(
            session,
            library_id=data.library_id,
            name=data.name,
            parent_id=data.parent_id,
            description=data.description,
        )
        await session.commit()
        return ApiResponse.success(data=FolderResponse.model_validate(folder).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/folders/{folder_id}/rename")
async def rename_folder(
    folder_id: str,
    data: FolderRename,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """重命名文件夹"""
    try:
        folder = await folder_service.rename(session, folder_id=folder_id, name=data.name)
        await session.commit()
        return ApiResponse.success(data=FolderResponse.model_validate(folder).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/folders/{folder_id}/move")
async def move_folder(
    folder_id: str,
    data: FolderMove,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """移动文件夹"""
    try:
        folder = await folder_service.move(session, folder_id=folder_id, new_parent_id=data.new_parent_id)
        await session.commit()
        return ApiResponse.success(data=FolderResponse.model_validate(folder).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """软删除文件夹（移入回收站）"""
    try:
        recycle_item_id = await folder_service.delete(session, folder_id=folder_id)
        await session.commit()
        return ApiResponse.success(data={"recycle_item_id": recycle_item_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
