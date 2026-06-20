"""会话管理 Schema

定义会话列表和删除接口的请求/响应 Schema。
"""

from datetime import datetime

from framework.schemas import BaseModel
from pydantic import Field


class ConversationListItem(BaseModel):
    """会话列表项 Schema"""

    id: str = Field(description="会话 ID")
    name: str = Field(description="会话名称")
    created_at: datetime = Field(description="创建时间")
    message_count: int = Field(default=0, description="消息数量")


class ConversationListResponse(BaseModel):
    """会话列表响应 Schema"""

    conversations: list[ConversationListItem] = Field(default_factory=list, description="会话列表")


class ConversationDeleteResponse(BaseModel):
    """会话删除响应 Schema"""

    success: bool = Field(description="是否成功")
