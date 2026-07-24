"""用户端元数据控制器"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.metadata import (
    MetadataFieldDefine,
    MetadataSet,
    MetadataBatchSet,
    MetadataSearchQuery,
    MetadataFieldResponse,
    ResourceMetadataResponse,
)
from document.services.metadata_service import metadata_service

router = APIRouter()


@router.post("/libraries/{library_id}/metadata-fields")
async def define_field(
    library_id: str,
    data: MetadataFieldDefine,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """定义元数据字段"""
    try:
        field = await metadata_service.define_field(
            session,
            library_id=library_id,
            name=data.name,
            field_type=data.field_type,
            is_required=data.is_required,
            enum_values=data.enum_values,
            sort_order=data.sort_order,
        )
        await session.commit()
        return ApiResponse.success(data=MetadataFieldResponse.model_validate(field).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/libraries/{library_id}/metadata-fields")
async def list_fields(
    library_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看元数据字段列表"""
    fields = await metadata_service.list_fields(session, library_id=library_id)
    return ApiResponse.success(
        data=[MetadataFieldResponse.model_validate(f).model_dump() for f in fields]
    )


@router.post("/metadata")
async def set_metadata(
    data: MetadataSet,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """设置资源元数据"""
    try:
        metadata = await metadata_service.set_metadata(
            session,
            library_id=data.library_id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            field_id=data.field_id,
            field_name=data.field_name,
            value=data.value,
        )
        await session.commit()
        return ApiResponse.success(data=ResourceMetadataResponse.model_validate(metadata).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/metadata/batch")
async def batch_set_metadata(
    data: MetadataBatchSet,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """批量设置元数据"""
    try:
        items_dicts = [item.model_dump() for item in data.items]
        results = await metadata_service.batch_set(
            session,
            library_id=data.library_id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            items=items_dicts,
        )
        await session.commit()
        return ApiResponse.success(
            data=[ResourceMetadataResponse.model_validate(r).model_dump() for r in results]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/libraries/{library_id}/resources/{resource_type}/{resource_id}/metadata")
async def query_metadata(
    library_id: str,
    resource_type: str,
    resource_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询资源元数据"""
    metadata_list = await metadata_service.query_metadata(
        session,
        library_id=library_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    return ApiResponse.success(
        data=[ResourceMetadataResponse.model_validate(m).model_dump() for m in metadata_list]
    )


@router.get("/metadata/search")
async def search_by_metadata(
    query: MetadataSearchQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """按元数据搜索资源"""
    items, total = await metadata_service.search_by_metadata(
        session,
        library_id=query.library_id,
        field_name=query.field_name,
        value=query.value,
        resource_type=query.resource_type,
        page=query.page,
        page_size=query.page_size,
    )
    return ApiResponse.paginated(
        data=[ResourceMetadataResponse.model_validate(m).model_dump() for m in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
