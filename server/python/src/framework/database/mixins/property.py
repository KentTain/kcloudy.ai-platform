"""
属性配置混入

提供属性容器和属性值的通用字段。
"""

from enum import Enum

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from framework.database.types.enum import EnumType


class AttributeDataType(str, Enum):
    """
    属性数据类型枚举

    用于指导属性值的类型转换。
    """

    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE_TIME = "date_time"
    BOOLEAN = "boolean"
    JSON = "json"


class PropertyMixin:
    """
    属性容器混入类

    提供属性容器的通用字段：
    - name: 名称
    - display_name: 显示名称
    - description: 描述
    - can_edit: 是否能编辑
    - is_require: 是否必须
    - index: 排序
    """

    __abstract__ = True

    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="名称"
    )

    display_name: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="显示名称"
    )

    description: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
        comment="描述"
    )

    can_edit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否能编辑"
    )

    is_require: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否必须"
    )

    index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序"
    )


class PropertyAttributeMixin:
    """
    属性值混入类

    提供属性值的通用字段：
    - data_type: 属性数据类型
    - name: 属性值名称
    - display_name: 显示名称
    - description: 描述
    - value: 属性值（字符串形式）
    - ext_data: 扩展数据（JSONB）
    - can_edit: 是否能编辑
    - is_require: 是否必须
    - index: 排序
    """

    __abstract__ = True

    data_type: Mapped[str] = mapped_column(
        EnumType(enum_class=AttributeDataType, length=20),
        nullable=False,
        default=AttributeDataType.STRING.value,
        comment="属性数据类型"
    )

    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="属性值名称"
    )

    display_name: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="显示名称"
    )

    description: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
        comment="描述"
    )

    value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="属性值"
    )

    ext_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="扩展数据"
    )

    can_edit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否能编辑"
    )

    is_require: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否必须"
    )

    index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序"
    )
