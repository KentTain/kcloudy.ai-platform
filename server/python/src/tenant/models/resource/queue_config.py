"""
队列配置模型
"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from tenant.models import BaseModel


class QueueConfig(BaseModel):
    """队列配置模型"""

    __tablename__ = "queue_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="配置名称")
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="队列类型（redis/rabbitmq/kafka）"
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False, comment="队列主机")
    port: Mapped[int] = mapped_column(nullable=False, comment="队列端口")
    username: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="用户名"
    )
    password: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="密码（加密）"
    )
    vhost: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="虚拟主机"
    )
    is_default: Mapped[bool] = mapped_column(Boolean,
        nullable=False, server_default="false", comment="是否为默认配置"
    )

    __table_args__ = (
        Index("ix_queue_configs_name", "name"),
        {"comment": "队列配置表"},
    )
