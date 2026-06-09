"""
模块定义模型
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class Module(BaseModel):
    """模块定义模型"""

    __tablename__ = "modules"

    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="模块编码"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模块名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="模块描述"
    )
    icon: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="图标标识"
    )
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0.0", comment="模块版本"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
    is_need: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否必须模块"
    )
