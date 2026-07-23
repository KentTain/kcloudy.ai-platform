"""document 模型可映射测试（验证表结构可创建）"""

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from document.models import Base


def test_all_models_can_create_table():
    """所有 document 模型可生成 DDL（验证字段/类型可映射）"""
    # 使用 PostgreSQL 方言编译以支持 JSONB 类型验证
    compiled_count = 0
    for table in Base.metadata.sorted_tables:
        if table.schema == "document":
            # 使用 PostgreSQL 方言编译 DDL，验证字段类型可映射
            CreateTable(table).compile(dialect=postgresql.dialect())
            compiled_count += 1
    # 至少应有一张表被编译，避免空通过
    assert compiled_count > 0, "未找到 document schema 的表，请检查模型导入"
