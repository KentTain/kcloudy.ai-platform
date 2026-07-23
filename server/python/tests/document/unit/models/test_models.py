"""document 模型可映射测试（验证表结构可创建）"""

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from document.models import Base


def test_all_models_can_create_table():
    """所有 document 模型可生成 DDL（验证字段/类型可映射）"""
    # 使用 create_engine 仅用于绑定元数据；实际编译使用 PostgreSQL 方言，
    # 因为模型使用了 PostgreSQL 专有的 JSONB 类型，sqlite 方言下编译 JSONB 不稳定。
    create_engine("sqlite://")
    compiled_count = 0
    for table in Base.metadata.sorted_tables:
        if table.schema == "document":
            # 使用 PostgreSQL 方言编译 DDL，验证字段类型可映射
            CreateTable(table).compile(dialect=postgresql.dialect())
            compiled_count += 1
    # 至少应有一张表被编译，避免空通过
    assert compiled_count > 0, "未找到 document schema 的表，请检查模型导入"
