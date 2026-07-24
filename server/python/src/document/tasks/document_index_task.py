"""文档切片索引任务触发"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Document
from document.models.enums import DocumentProcessingStatus


async def trigger_index_task(session: AsyncSession, document_id: str) -> str:
    """
    触发文档切片索引任务。

    document 只记录状态，实际 Embedding 由 ai 模块执行。
    Phase 3 完成后通过 ai inner 接口或事件触发。
    """
    stmt = select(Document).where(Document.id == document_id)
    doc = (await session.execute(stmt)).scalar_one_or_none()
    if doc is None:
        raise ValueError("文档不存在")
    doc.processing_status = DocumentProcessingStatus.PARSING
    await session.flush()

    # TODO(phase3): 通过 ai inner 接口触发实际切片
    return document_id