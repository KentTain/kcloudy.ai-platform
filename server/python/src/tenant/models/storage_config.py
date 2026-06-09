"""
存储配置模型
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class StorageConfig(BaseModel):
    """存储配置模型"""

    __tablename__ = "storage_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="配置名称")
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="存储类型（minio/s3/oss）"
    )
    bucket: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="存储桶名称"
    )
    endpoint: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="服务端点"
    )
    access_key: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="访问密钥"
    )
    secret_key: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="私密密钥（加密）"
    )

    __table_args__ = (
        Index("ix_storage_configs_name", "name"),
    )
