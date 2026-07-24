"""用户端文档控制器"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_tenant_id
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.document import DocumentPaginatedQuery, DocumentMove, DocumentResponse
from document.services.document_service import document_service

router = APIRouter()


@router.get("/documents")
async def list_documents(
    query: DocumentPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查看文档列表"""
    items, total = await document_service.list_documents(
        session,
        library_id=query.library_id,
        folder_id=query.folder_id,
        page=query.page,
        page_size=query.page_size,
    )
    return ApiResponse.paginated(
        data=[DocumentResponse.model_validate(doc).model_dump() for doc in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.post("/documents/upload")
async def upload_document(
    library_id: str,
    folder_id: str | None = None,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """上传文档"""
    content = await file.read()
    try:
        doc = await document_service.upload(
            session,
            library_id=library_id,
            folder_id=folder_id,
            filename=file.filename or "untitled",
            content=content,
            mime_type=file.content_type,
        )
        await session.commit()
        return ApiResponse.success(data=DocumentResponse.model_validate(doc).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取文档详情"""
    doc = await document_service.get_by_id(session, doc_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return ApiResponse.success(data=DocumentResponse.model_validate(doc).model_dump())


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """软删除文档"""
    try:
        await document_service.soft_delete(session, doc_id=document_id)
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/documents/{document_id}/move")
async def move_document(
    document_id: str,
    data: DocumentMove,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """移动文档"""
    tenant_id = get_tenant_id()
    try:
        doc = await document_service.move(
            session,
            doc_id=document_id,
            target_folder_id=data.target_folder_id,
            tenant_id=tenant_id,
        )
        await session.commit()
        return ApiResponse.success(data=DocumentResponse.model_validate(doc).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{document_id}/trigger-index")
async def trigger_index(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """触发文档索引任务"""
    tenant_id = get_tenant_id()
    try:
        await document_service.trigger_index_task(
            session,
            doc_id=document_id,
            tenant_id=tenant_id,
        )
        await session.commit()
        return ApiResponse.success()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
