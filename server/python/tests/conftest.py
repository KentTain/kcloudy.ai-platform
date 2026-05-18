import logging
import os


# 设置环境变量
os.environ["PYTHON_SERVICE_ENV"] = "local"
# 设置时区
os.environ["TZ"] = "Asia/Shanghai"

import asyncio

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from demo.configs.settings import settings
from demo.models import BaseModel


# 配置 SQLAlchemy 相关日志级别
for logger_name in [
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.engine.base",
    "sqlalchemy.engine.Engine",
    "sqlalchemy.pool",
    "sqlalchemy.log",
    "sqlalchemy.orm",
    "aiosqlite",
    "databases",
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)
    logging.getLogger(logger_name).propagate = False

# 禁用 alembic 的日志
logging.getLogger("alembic").setLevel(logging.WARNING)

# 设置根日志级别为 WARNING
logging.basicConfig(level=logging.WARNING, force=True)

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="module")
def event_loop():
    """
    为每个测试用例创建一个默认事件循环的实例

    Returns:
        asyncio.AbstractEventLoop: 新创建的事件循环实例
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def async_engine():
    """
    创建异步数据库引擎（只执行一次）

    注意：
        - 使用 session 作用域，确保所有测试用例使用同一个数据库引擎
        - 测试类执行完毕后会自动关闭引擎
        - 测试方法中不应该修改引擎状态，除非显式提交

    Returns:
        AsyncEngine: 异步数据库引擎实例
    """
    engine = create_async_engine(
        url=settings.sqlalchemy.database_url,
        echo=settings.sqlalchemy.echo,
        pool_pre_ping=True,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield engine
    # 不再在测试结束时删除所有表，避免影响真实数据库
    await engine.dispose()


# 注意：这里使用 class 作用域而不是 session 作用域，因为：
# 1. 测试类之间需要隔离的数据库状态
# 2. 避免测试之间的状态污染
# 3. 虽然性能略低于 session 作用域，但能提供更好的测试隔离性
# 4. 与测试类中的其他 class 作用域 fixture 保持一致
@pytest_asyncio.fixture(scope="class")
async def async_session(async_engine):
    """
    创建一个异步数据库会话

    注意：
        - 使用 class 作用域，确保每个测试类只创建一个会话
        - 这样可以在测试类中的多个测试方法之间共享数据库状态
        - 测试完成后会自动回滚事务，确保测试隔离
    """
    # 直接使用 async_engine 创建会话
    async with AsyncSession(bind=async_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(scope="class")
async def cleanup_resources():
    """
    通用的资源清理fixture，处理清理逻辑中的错误

    注意：
        - 使用 class 作用域，确保与测试类中的其他 fixture 兼容
        - 处理清理操作中的错误和事务管理

    Yields:
        Callable: 清理函数，接收清理回调函数、会话和资源数据
                返回一个元组 (success_count, error_count)
    """

    async def _cleanup(cleanup_func, *args, **kwargs):
        """
        执行清理操作并处理错误

        Args:
            cleanup_func: 执行实际清理的回调函数
            *args, **kwargs: 传递给清理函数的参数

        Returns:
            tuple: (成功数量, 失败数量)
        """
        try:
            # 执行清理
            success = await cleanup_func(*args, **kwargs)
            if success:
                logger.info("✅ =======cleanup_resources：清理成功")
                return 1, 0
            else:
                logger.error("❌ =======cleanup_resources：清理失败: 操作返回False")
                return 0, 1
        except Exception as e:
            logger.error(
                f"❌ =======cleanup_resources：清理时发生错误: {str(e)}", exc_info=True
            )
            return 0, 1

    yield _cleanup
