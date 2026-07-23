"""
站内信相关 Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


class NotificationPaginatedQuery(BasePaginatedQuery):
    """站内信分页查询参数"""

    is_read: bool | None = Field(default=None, description="是否已读")
    notification_type: str | None = Field(default=None, description="通知类型")


class NotificationResponse(BaseModel):
    """站内信视图对象"""

    id: str
    title: str = Field(description="通知标题")
    content: str | None = Field(default=None, description="通知内容")
    notification_type: str = Field(description="通知类型")
    recipient_id: str = Field(description="接收人ID")
    sender_id: str | None = Field(default=None, description="发送人ID")
    link: str | None = Field(default=None, description="跳转链接")
    extra_data: dict[str, Any] | None = Field(default=None, description="扩展数据")
    is_read: bool = Field(description="是否已读")
    read_at: datetime | None = Field(default=None, description="已读时间")
    created_at: datetime = Field(description="创建时间")


class NotificationMarkReadRequest(BaseModel):
    """标记站内信已读请求"""

    notification_ids: list[str] = Field(description="通知ID列表")


class NotificationUnreadCountResponse(BaseModel):
    """站内信未读数量响应"""

    unread_count: int = Field(description="未读数量")
