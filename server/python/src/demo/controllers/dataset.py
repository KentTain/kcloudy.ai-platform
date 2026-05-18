"""
Dataset Controller
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from demo.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetVo
from demo.services.dataset import dataset_service

router = APIRouter()


def Success(data: dict | list | None = None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


@router.get("")
async def list_datasets(page: int = 1, page_size: int = 10) -> ORJSONResponse:
    """获取知识库列表"""
    total, datasets = await dataset_service.list_datasets(page, page_size)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [DatasetVo.model_validate(d).model_dump() for d in datasets],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("")
async def create_dataset(data: DatasetCreate) -> ORJSONResponse:
    """创建知识库"""
    dataset = await dataset_service.create_dataset(data)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": DatasetVo.model_validate(dataset).model_dump(),
        }
    )


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str) -> ORJSONResponse:
    """获取知识库详情"""
    dataset = await dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": DatasetVo.model_validate(dataset).model_dump(),
        }
    )


@router.put("/{dataset_id}")
async def update_dataset(dataset_id: str, data: DatasetUpdate) -> ORJSONResponse:
    """更新知识库"""
    dataset = await dataset_service.update_dataset(dataset_id, data)
    if not dataset:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": DatasetVo.model_validate(dataset).model_dump(),
        }
    )


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str) -> ORJSONResponse:
    """删除知识库"""
    success = await dataset_service.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ORJSONResponse(content={"code": 200, "msg": "success"})
