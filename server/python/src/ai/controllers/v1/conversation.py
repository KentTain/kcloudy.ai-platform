"""会话管理控制器

提供会话列表和删除接口。
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlalchemy import func, select

from ai.models.conversation import Conversation
from ai.models.enums import ConversationStatus
from ai.models.message import Message
from ai.schemas.conversation import (
    ConversationDeleteResponse,
    ConversationListItem,
    ConversationListResponse,
)
from framework.common.ctx import get_tenant_id
from framework.database.core.engine import get_session

_logger = logger.bind(name=__name__)

router = APIRouter(prefix="/conversations", tags=["会话管理"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations() -> ConversationListResponse:
    """获取会话列表

    返回当前租户的所有会话，按创建时间倒序排列。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=401, detail="未授权访问")

    try:
        async with get_session() as session:
            # 查询会话及其消息数量
            # 使用子查询统计消息数量
            message_count_subquery = (
                select(
                    Message.conversation_id,
                    func.count(Message.id).label("count"),
                )
                .where(Message.tenant_id == tenant_id)
                .group_by(Message.conversation_id)
                .subquery()
            )

            # 查询会话列表
            stmt = (
                select(
                    Conversation.id,
                    Conversation.name,
                    Conversation.created_at,
                    func.coalesce(message_count_subquery.c.count, 0).label("message_count"),
                )
                .outerjoin(
                    message_count_subquery,
                    Conversation.id == message_count_subquery.c.conversation_id,
                )
                .where(
                    Conversation.tenant_id == tenant_id,
                    Conversation.status != ConversationStatus.DELETED,
                )
                .order_by(Conversation.created_at.desc())
            )

            result = await session.execute(stmt)
            rows = result.all()

            conversations = [
                ConversationListItem(
                    id=str(row.id),
                    name=row.name,
                    created_at=row.created_at,
                    message_count=row.message_count,
                )
                for row in rows
            ]

            return ConversationListResponse(conversations=conversations)

    except Exception as e:
        _logger.exception("获取会话列表失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(conversation_id: str) -> ConversationDeleteResponse:
    """删除会话

    软删除指定会话（将状态设为 DELETED）。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=401, detail="未授权访问")

    try:
        async with get_session() as session:
            # 查询会话
            conversation = await Conversation.one_by_conditions(
                session,
                conditions=[
                    Conversation.id == conversation_id,
                    Conversation.tenant_id == tenant_id,
                ],
            )

            if not conversation:
                raise HTTPException(status_code=404, detail="会话不存在")

            # 软删除：更新状态为 DELETED
            conversation.status = ConversationStatus.DELETED
            await session.commit()

            return ConversationDeleteResponse(success=True)

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("删除会话失败")
        raise HTTPException(status_code=500, detail=str(e))
