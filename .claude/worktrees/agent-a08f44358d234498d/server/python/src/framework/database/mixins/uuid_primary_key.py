"""
UUID 主键混入

提供 UUID 格式的主键字段。
"""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """
    UUID 主键混入类

    提供 UUID 格式的主键字段，使用 36 字符字符串存储。
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID",
    )
