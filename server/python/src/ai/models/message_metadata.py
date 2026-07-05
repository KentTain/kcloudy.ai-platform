"""消息元数据模型"""

from sqlalchemy import Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel


class MessageMetadata(BaseModel):
    """消息元数据模型"""

    __tablename__ = "message_metadata"
    __table_args__ = ({"schema": "ai", "comment": "消息元数据"},)

    message_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="消息ID"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="租户ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="用户ID"
    )

    # 用户反馈
    rating: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="评分：1=👎, 2=👍"
    )
    feedback: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="反馈文本"
    )

    # 使用统计
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="提示词token数"
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="补全token数"
    )
    total_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="总token数"
    )
    model_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="模型名称"
    )
    provider: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="提供商"
    )
    response_time_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="响应时间(毫秒)"
    )