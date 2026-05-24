"""
框架 Schema 模块

提供统一的 Pydantic VO 基类。
"""

from framework.schemas.tree import TreeNodeVo, TreeNodeTreeVo

__all__ = [
    "TreeNodeVo",
    "TreeNodeTreeVo",
]