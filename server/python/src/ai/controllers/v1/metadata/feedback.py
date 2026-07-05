"""消息反馈控制器

提供消息反馈的提交和更新接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.message_metadata import MessageMetadata
from ai.schemas.metadata import FeedbackResponse, SubmitFeedbackRequest
from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext
from iam.dependencies import get_current_user_id

router = APIRouter()
_logger = logger.bind(name=__name__)


@router.post("/feedback")
async def submit_feedback(
    request: SubmitFeedbackRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
) -> ORJSONResponse:
    """提交消息反馈"""

    tenant_id = TenantContext.get_tenant_id()

    # 检查是否已存在
    result = await session.execute(
        select(MessageMetadata).where(
            MessageMetadata.message_id == request.message_id,
            MessageMetadata.tenant_id == tenant_id,
        )
    )
    metadata = result.scalar_one_or_none()

    if metadata:
        # 更新反馈
        metadata.rating = request.rating
        metadata.feedback = request.feedback
        _logger.info(f"Updated feedback for message {request.message_id}")
    else:
        # 创建新记录
        metadata = MessageMetadata(
            message_id=request.message_id,
            tenant_id=tenant_id,
            user_id=user_id,
            rating=request.rating,
            feedback=request.feedback,
        )
        session.add(metadata)
        _logger.info(f"Created feedback for message {request.message_id}")

    await session.commit()

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "反馈提交成功",
            "data": FeedbackResponse(
                message_id=metadata.message_id,
                rating=metadata.rating,
                feedback=metadata.feedback,
                created_at=metadata.created_at.isoformat(),
            ).model_dump(),
        }
    )