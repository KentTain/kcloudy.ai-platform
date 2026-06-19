"""
缓存配置模型
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class CacheConfig(BaseModel):
    """缓存配置模型"""

    __tablename__ = "cache_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="配置名称")
    host: Mapped[str] = mapped_column(String(255), nullable=False, comment="缓存主机")
    port: Mapped[int] = mapped_column(nullable=False, comment="缓存端口")
    password: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="缓存密码（加密）"
    )
    db: Mapped[int] = mapped_column(nullable=False, default=0, comment="数据库编号")
    prefix: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="键前缀"
    )

    __table_args__ = (
        Index("ix_cache_configs_name", "name"),
    )
