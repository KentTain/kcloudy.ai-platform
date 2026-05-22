"""
数据库模型基础类

重导出 framework.database 中的基础组件。
"""

from framework.database import ActiveRecordMixin, Base, BaseModel

__all__ = [
    "Base",
    "BaseModel",
    "ActiveRecordMixin",
]
