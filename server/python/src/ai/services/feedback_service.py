"""反馈服务

提供反馈提交和更新的业务逻辑封装。
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ai.models.message_metadata import MessageMetadata
from ai.schemas.metadata import SubmitFeedbackRequest

_logger = logger.bind(name=__name__)


class FeedbackService:
    """反馈服务

    提供反馈的提交、更新等业务逻辑方法。
    """

    async def submit_feedback(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        request: SubmitFeedbackRequest,
    ) -> MessageMetadata:
        """提交或更新反馈

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            user_id: 用户 ID
            request: 反馈请求

        Returns:
            MessageMetadata: 消息元数据对象
        """
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

        await session.flush()
        await session.refresh(metadata)
        return metadata


# 服务单例
feedback_service = FeedbackService()