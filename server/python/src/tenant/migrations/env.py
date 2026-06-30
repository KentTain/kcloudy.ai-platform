"""
Alembic 环境配置 - Tenant 模块

配置独立的迁移版本表在 tenant schema 下。
"""

import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tenant.models import Base

config = context.config

# 从配置中获取数据库 URL
try:
    from framework.configs import get_settings

    settings = get_settings()
    db_url = settings.sqlalchemy.url
    config.set_main_option("sqlalchemy.url", db_url)
except Exception as e:
    print(f"[WARN] 无法从配置加载数据库 URL: {e}")
    print("[INFO] 使用 alembic.ini 中的默认配置")

# 注意：不调用 fileConfig()，避免 raw=True 导致 %% 未转换的问题
# 应用层日志配置已足够，Alembic 的日志会继承根日志器的配置

# Tenant 模块的 metadata
target_metadata = Base.metadata

# 模块 schema 名称
MODULE_SCHEMA = "tenant"


def _include_name(name, type_, parent_names):
    """Schema 过滤：仅检查 tenant schema 中的对象

    Alembic autogenerate 默认检查所有 schema 的对象。
    此过滤器将范围限定为 tenant schema，避免与其他模块的 schema 产生冲突。
    """
    if type_ == "schema":
        return name == MODULE_SCHEMA
    return True


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 版本表在 tenant schema
        version_table_schema=MODULE_SCHEMA,
        # 禁用类型比较：框架自定义类型（StringUUID、EnumType）在数据库中存储为 VARCHAR，
        # 启用类型比较会导致 Alembic 生成冗余的 ALTER COLUMN 迁移
        compare_type=False,
        include_schemas=True,
        include_name=_include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 版本表在 tenant schema
        version_table_schema=MODULE_SCHEMA,
        # 禁用类型比较
        compare_type=False,
        include_schemas=True,
        include_name=_include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # 确保 schema 存在
        from sqlalchemy import text
        await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}"))
        await connection.commit()

        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    # 检测是否已经在事件循环中运行
    try:
        loop = asyncio.get_running_loop()
        # 如果已在事件循环中，创建任务并等待完成
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(run_async_migrations())
    except RuntimeError:
        # 没有运行中的事件循环，使用 asyncio.run()
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
