"""
Dataset 示例模型
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from demo.models import (
    ActiveRecordMixin,
    BaseModel,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Dataset(
    BaseModel,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    ActiveRecordMixin,
):
    """知识库模型"""

    __tablename__ = "dataset"

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="知识库名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="知识库描述"
    )
