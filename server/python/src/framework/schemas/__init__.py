"""
框架 Schema 模块

提供统一的 Pydantic VO 基类。
"""

from framework.schemas.base import (
    AuditedOperatorVoMixin,
    BaseModel,
    BaseQueryParams,
    I18nConvertibleBaseModel,
    PropertyAttributeVoMixin,
    PropertyVoMixin,
    VoMixin,
)
from framework.schemas.tree import TreeNodeTreeVo, TreeNodeVo, TreeNodeVoMixin

__all__ = [
    # 基类
    "BaseModel",
    "BaseQueryParams",
    "VoMixin",
    # Mixin
    "TreeNodeVoMixin",
    "AuditedOperatorVoMixin",
    "PropertyVoMixin",
    "PropertyAttributeVoMixin",
    "I18nConvertibleBaseModel",
    # 树 VO
    "TreeNodeVo",
    "TreeNodeTreeVo",
]
