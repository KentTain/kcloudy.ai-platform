import logging
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径（必须在导入 demo 之前）
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Set environment variables
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

# 设置配置文件目录（测试使用 server/config/）
config_dir = Path(__file__).parent.parent.parent / "config"
if config_dir.exists():
    os.environ["APP_CONFIG_DIR"] = str(config_dir)

# =============================================================================
# Windows 事件循环策略修复
# =============================================================================
# Windows 上 ProactorEventLoop 与 pytest-asyncio 存在兼容性问题
# 使用 WindowsSelectorEventLoopPolicy 解决事件循环关闭后的连接问题
if sys.platform == "win32":
    if hasattr(__import__('asyncio'), 'WindowsSelectorEventLoopPolicy'):
        __import__('asyncio').set_event_loop_policy(
            __import__('asyncio').WindowsSelectorEventLoopPolicy()
        )


import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from demo.configs import settings
from demo.models import BaseModel

# Configure SQLAlchemy logging levels
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

logging.getLogger("alembic").setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING, force=True)

logger = logging.getLogger(__name__)


# ===== Optional dependency handling =====
def _has_langchain_deps():
    try:
        import langchain_core  # noqa: F401
        import langgraph  # noqa: F401
        return True
    except ImportError:
        return False


HAS_LANGCHAIN = _has_langchain_deps()


def pytest_ignore_collect(collection_path, config):
    """
    Skip collection of langchain-related tests when dependencies are missing.
    Prevents ImportError during test discovery.
    """
    if HAS_LANGCHAIN:
        return False

    path_str = str(collection_path).replace("\\", "/")
    langchain_paths = [
        "/tests/demo/examples/",
        "/tests/demo/studies/langchain_study/",
        "/tests/demo/studies/langgraph_study/",
        "/tests/extended/langchain/",
        "/tests/ai/controllers/v1/chat/test_llm.py",
        "/tests/ai/unit/controllers/v1/chat/test_llm.py",
    ]

    for skip_path in langchain_paths:
        if skip_path in path_str:
            return True

    return False


# ===== Fixtures =====

# 使用 pytest-asyncio 自动管理 event_loop，不再手动定义
# pytest.ini_options 中配置了 asyncio_mode = "auto"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def async_engine():
    import asyncio

    engine = create_async_engine(
        url=settings.sqlalchemy.url,
        echo=settings.sqlalchemy.echo,
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield engine

    # 安全关闭引擎，处理事件循环已关闭的情况
    try:
        loop = asyncio.get_running_loop()
        if not loop.is_closed():
            await engine.dispose()
    except RuntimeError:
        pass


@pytest_asyncio.fixture(scope="class", loop_scope="class")
async def async_session(async_engine):
    async with AsyncSession(bind=async_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(scope="class", loop_scope="class")
async def cleanup_resources():
    async def _cleanup(cleanup_func, *args, **kwargs):
        try:
            success = await cleanup_func(*args, **kwargs)
            if success:
                logger.info("Cleanup succeeded")
                return 1, 0
            else:
                logger.error("Cleanup failed: operation returned False")
                return 0, 1
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}", exc_info=True)
            return 0, 1

    yield _cleanup
