"""
数据库 Session 依赖注入

提供多租户感知的 FastAPI 依赖注入函数和 Listener/Task 专用函数。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.core.engine_pool import get_engine_pool
from framework.tenant.context import TenantContext


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（多租户感知）

    用于 Controller 层，通过 FastAPI Depends 注入。

    自动根据 TenantContext 选择正确的数据库引擎：
    - 逻辑隔离：使用默认引擎，通过 tenant_id 字段过滤
    - 物理隔离：使用租户专属引擎

    事务管理：
    - 成功时自动 commit
    - 异常时自动 rollback

    Yields:
        AsyncSession: 数据库会话
    """
    tenant_id = TenantContext.get_tenant_id()
    db_config = TenantContext.get_database_config()

    pool = get_engine_pool()
    async with pool.session(tenant_id, db_config) as session:
        try:
            yield session
        except Exception:
            raise


@asynccontextmanager
async def get_listener_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取 Listener 专用数据库会话（多租户感知）

    用于消息监听器，需要在消息处理前设置 TenantContext。

    使用示例：
        async def handle(self, message: dict) -> None:
            TenantContext.set_tenant_id(message["tenant_id"])
            async with get_listener_session() as session:
                await service.method(session, ...)

    Yields:
        AsyncSession: 数据库会话
    """
    from framework.database.core.engine_pool import get_engine_pool
    from framework.tenant.context import TenantContext

    tenant_id = TenantContext.get_tenant_id()
    db_config = TenantContext.get_database_config()

    pool = get_engine_pool()
    async with pool.session(tenant_id, db_config) as session:
        try:
            yield session
        except Exception:
            raise


@asynccontextmanager
async def get_task_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取 Task 专用数据库会话（多租户感知）

    用于定时任务，需要在任务执行时根据业务需求设置 TenantContext。

    使用示例：
        async def my_task():
            # 方式1：操作默认数据库（无租户上下文）
            async with get_task_session() as session:
                await service.method(session, ...)

            # 方式2：操作特定租户数据
            TenantContext.set_tenant_id("tenant-001")
            async with get_task_session() as session:
                await service.method(session, ...)

    Yields:
        AsyncSession: 数据库会话
    """
    from framework.database.core.engine_pool import get_engine_pool
    from framework.tenant.context import TenantContext

    tenant_id = TenantContext.get_tenant_id()
    db_config = TenantContext.get_database_config()

    pool = get_engine_pool()
    async with pool.session(tenant_id, db_config) as session:
        try:
            yield session
        except Exception:
            raise
