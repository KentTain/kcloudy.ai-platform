"""
企业知识库管理模块数据库模型
"""

from framework.database.core import create_base_model, create_module_base

# 创建模块级 Base，指定 schema 为 "document"
Base = create_module_base(schema="document")

# 创建数据模型基类
BaseModel = create_base_model(Base)

__all__ = ["Base", "BaseModel"]
