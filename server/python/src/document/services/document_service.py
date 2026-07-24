"""文档服务"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Document
from document.models.enums import DocumentStatus
from framework.common.ctx import get_tenant_id, get_user_id
from framework.storage.tenant_storage import TenantMinioStorage


# 默认存储桶名称
_DEFAULT_BUCKET = "document"


class DocumentService:
    """文档服务"""

    @staticmethod
    async def upload(
        session: AsyncSession,
        library_id: str,
        folder_id: str | None,
        filename: str,
        content: bytes,
        mime_type: str | None = None,
    ) -> Document:
        """上传文件到 MinIO 并创建 Document 记录"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        # 上传到 MinIO（租户感知路径）
        storage_key = await TenantMinioStorage.upload(
            bucket=_DEFAULT_BUCKET,
            name=f"document/{library_id}/{filename}",
            data=content,
            content_type=mime_type,
        )

        doc = Document(
            tenant_id=tenant_id,
            library_id=library_id,
            folder_id=folder_id,
            owner_id=user_id,
            storage_key=storage_key,
            name=filename,
            document_type="document",
            lifecycle_status=DocumentStatus.UPLOADING,
            file_size=len(content),
            mime_type=mime_type,
        )
        session.add(doc)
        await session.flush()
        return doc

    @staticmethod
    async def get_by_id(session: AsyncSession, doc_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == doc_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def list_documents(
        session: AsyncSession,
        library_id: str,
        folder_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Document], int]:
        conditions = [Document.library_id == library_id]
        if folder_id:
            conditions.append(Document.folder_id == folder_id)
        total = (await session.execute(
            select(func.count(Document.id)).where(*conditions)
        )).scalar() or 0
        offset = (page - 1) * page_size
        stmt = select(Document).where(*conditions).offset(offset).limit(page_size)
        return list((await session.execute(stmt)).scalars().all()), total

    @staticmethod
    async def soft_delete(session: AsyncSession, doc_id: str) -> None:
        """软删除文档（设置 lifecycle_status=trashed）"""
        doc = await DocumentService.get_by_id(session, doc_id)
        if doc is None:
            raise ValueError("文档不存在")
        doc.lifecycle_status = DocumentStatus.TRASHED
        await session.flush()


document_service = DocumentService()
