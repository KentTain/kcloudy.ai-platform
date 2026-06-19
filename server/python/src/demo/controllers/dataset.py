"""
Dataset Controller

使用依赖注入模式，session 通过 FastAPI Depends 注入。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from demo.schemas.dataset import DatasetCreate, DatasetResponse, DatasetUpdate
from demo.services.dataset import dataset_service
from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra

router = APIRouter()


@router.get("")
async def list_datasets(
    page: int = 1,
    page_size: int = 10,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取知识库列表"""
    total, datasets = await dataset_service.list_datasets(session, page, page_size)
    return SuccessExtra(
        data=[DatasetResponse.model_validate(d).model_dump() for d in datasets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_dataset(
    data: DatasetCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建知识库"""
    dataset = await dataset_service.create_dataset(session, data)
    return Success(data=DatasetResponse.model_validate(dataset).model_dump())


@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取知识库详情"""
    dataset = await dataset_service.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return Success(data=DatasetResponse.model_validate(dataset).model_dump())


@router.put("/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    data: DatasetUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新知识库"""
    dataset = await dataset_service.update_dataset(session, dataset_id, data)
    if not dataset:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return Success(data=DatasetResponse.model_validate(dataset).model_dump())


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除知识库"""
    success = await dataset_service.delete_dataset(session, dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return Success(data=success)
