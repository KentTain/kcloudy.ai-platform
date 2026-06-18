"""
数据库配置模型
"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class DatabaseConfig(BaseModel):
    """数据库配置模型"""

    __tablename__ = "database_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="配置名称")
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="数据库类型（postgresql/mysql）"
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False, comment="数据库主机")
    port: Mapped[int] = mapped_column(nullable=False, comment="数据库端口")
    database: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="数据库名称"
    )
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="数据库用户名"
    )
    password: Mapped[str] = mapped_column(
        Text, nullable=False, comment="数据库密码（加密）"
    )
    is_default: Mapped[bool] = mapped_column(Boolean,
        nullable=False, server_default="false", comment="是否为默认配置"
    )

    __table_args__ = (
        Index("ix_database_configs_name", "name"),
    )
