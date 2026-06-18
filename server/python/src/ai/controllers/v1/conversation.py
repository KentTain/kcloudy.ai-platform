"""会话管理控制器

提供会话列表和删除接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.conversation import (
    ConversationDeleteResponse,
    ConversationListResponse,
)
from ai.services import conversation_service
from framework.common.ctx import get_tenant_id
from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra

_logger = logger.bind(name=__name__)

router = APIRouter(prefix="/conversations", tags=["会话管理"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationListResponse:
    """获取会话列表

    返回当前租户的所有会话，按创建时间倒序排列。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=401, detail="未授权访问")

    try:
        conversations = await conversation_service.list_with_message_count(
            session, tenant_id
        )
        return ConversationListResponse(conversations=conversations)

    except Exception as e:
        _logger.exception("获取会话列表失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ConversationDeleteResponse:
    """删除会话

    软删除指定会话（将状态设为 DELETED）。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=401, detail="未授权访问")

    try:
        success = await conversation_service.soft_delete(
            session, conversation_id, tenant_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return ConversationDeleteResponse(success=True)

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("删除会话失败")
        raise HTTPException(status_code=500, detail=str(e))
