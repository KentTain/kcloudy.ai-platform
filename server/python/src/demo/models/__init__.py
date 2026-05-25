"""
Demo 模块数据模型

包含演示模块的所有数据模型。
所有模型归属于 demo PostgreSQL schema。
"""

from framework.database import create_module_base, create_base_model
from framework.database.mixins.active_record import ActiveRecordMixin

# 创建 Demo 模块的 Base 和 BaseModel
Base = create_module_base("demo")
BaseModel = create_base_model(Base)

# 导入模型（必须在 Base 和 BaseModel 定义之后）
from .dataset import Dataset
from .enums import Status

__all__ = [
    "Base",
    "BaseModel",
    "ActiveRecordMixin",
    # 模型
    "Dataset",
    # 枚举
    "Status",
]
