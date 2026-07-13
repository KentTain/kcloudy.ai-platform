"""
Python 后端测试统一配置

提供所有模块共享的测试配置和 fixtures：
- 环境变量设置
- Windows 事件循环策略修复
- 日志配置
- 配置加载
- 服务可用性检测
- LangChain 依赖检测和测试跳过
- 通用 fixtures（数据库、Redis、MinIO）
- 工具函数
"""

import asyncio
import logging
import os
import socket
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# =============================================================================
# Python 路径设置
# =============================================================================

# 添加 src 目录到 Python 路径（必须在导入模块之前）
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# =============================================================================
# 环境变量设置
# =============================================================================

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
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =============================================================================
# 日志配置
# =============================================================================

# 配置 SQLAlchemy 日志级别
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

# 配置 Alembic 日志级别
logging.getLogger("alembic").setLevel(logging.WARNING)

# 配置根日志级别
logging.basicConfig(level=logging.WARNING, force=True)

logger = logging.getLogger(__name__)

# =============================================================================
# LangChain 依赖检测和测试跳过
# =============================================================================


def _has_langchain_deps():
    """检测是否安装了 LangChain 相关依赖"""
    try:
        import langchain_core  # noqa: F401
        import langgraph  # noqa: F401

        return True
    except ImportError:
        return False


HAS_LANGCHAIN = _has_langchain_deps()


def pytest_ignore_collect(collection_path, config):
    """
    跳过 LangChain 相关测试当依赖缺失时。

    防止测试发现阶段的 ImportError。
    """
    if HAS_LANGCHAIN:
        return False

    path_str = str(collection_path).replace("\\", "/")
    langchain_paths = [
        "/tests/demo/examples/",
        "/tests/demo/studies/langchain_study/",
        "/tests/demo/studies/langgraph_study/",
        "/tests/extended/langchain/",
        "/tests/ai/unit/controllers/v1/chat/test_llm.py",
    ]

    for skip_path in langchain_paths:
        if skip_path in path_str:
            return True

    return False


# =============================================================================
# 配置加载（模块级别，确保测试收集阶段配置已初始化）
# =============================================================================

# 在模块顶层初始化配置，防止测试导入阶段因配置未初始化而失败
_config_dir = Path(__file__).resolve().parent.parent.parent / "config"
if _config_dir.exists():
    from framework.configs import init_settings

    init_settings(_config_dir)


@pytest.fixture(scope="session")
def integration_settings():
    """
    返回已加载的集成测试配置（session 级别）。

    使用 server/config/application-local.yml
    """
    from framework.configs import get_settings

    return get_settings()


# =============================================================================
# 服务可用性检测（同步检测，避免事件循环问题）
# =============================================================================


def _check_redis_available(settings):
    """同步检测 Redis 服务是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((settings.redis.single.host, settings.redis.single.port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _check_postgres_available(settings):
    """同步检测 PostgreSQL 服务是否可用"""
    try:
        # 从 URL 中提取 host 和 port
        url = settings.sqlalchemy.url
        # postgresql+asyncpg://admin:password@host:port/database
        parts = url.split("@")[1].split("/")[0].split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5432

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _check_minio_available(settings):
    """同步检测 MinIO 服务是否可用"""
    try:
        from minio import Minio

        config = settings.oss.minio
        client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )
        # 尝试列出 buckets 来验证连接
        list(client.list_buckets())
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def redis_available(integration_settings):
    """检测 Redis 服务是否可用（session 级别，同步检测）"""
    return _check_redis_available(integration_settings)


@pytest.fixture(scope="session")
def postgres_available(integration_settings):
    """检测 PostgreSQL 服务是否可用（session 级别，同步检测）"""
    return _check_postgres_available(integration_settings)


@pytest.fixture(scope="session")
def minio_available(integration_settings):
    """检测 MinIO 服务是否可用（session 级别，同步检测）"""
    return _check_minio_available(integration_settings)


# =============================================================================
# 数据库 Fixtures（function 级别，确保每个测试都有独立的连接）
# =============================================================================


@pytest_asyncio.fixture
async def postgres_engine(integration_settings, postgres_available):
    """
    PostgreSQL 引擎 fixture（function 作用域）。

    每个测试获取独立的引擎，避免事件循环冲突。
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        integration_settings.sqlalchemy.url,
        echo=integration_settings.sqlalchemy.echo,
        pool_pre_ping=True,
        poolclass=NullPool,
    )

    yield engine

    # 安全关闭引擎
    try:
        await engine.dispose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def postgres_session(postgres_engine):
    """
    PostgreSQL 会话 fixture（function 作用域）。

    每个测试使用独立会话，测试结束后回滚。
    """
    async with AsyncSession(bind=postgres_engine) as session:
        try:
            yield session
            # 尝试提交，但忽略事件循环关闭错误
            try:
                await session.commit()
            except RuntimeError:
                pass  # 事件循环已关闭
        except Exception:
            try:
                await session.rollback()
            except RuntimeError:
                pass  # 事件循环已关闭
            raise


# =============================================================================
# Redis Fixtures（function 级别，确保每个测试都有独立的连接）
# =============================================================================


@pytest_asyncio.fixture
async def redis_client(integration_settings, redis_available):
    """
    Redis 客户端 fixture（function 作用域）。

    每个测试获取独立的 Redis 连接，避免事件循环冲突。
    这是在 Windows 上使用 pytest-asyncio 的最稳定方案。
    """
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    # 关闭现有连接（如果有）
    if RedisUtil.is_initialized():
        try:
            await RedisUtil.close()
        except Exception:
            pass

    # 初始化新连接
    await RedisUtil.init(integration_settings.redis)

    yield RedisUtil

    # 测试结束后关闭连接
    try:
        await RedisUtil.close()
    except Exception:
        pass


@pytest.fixture
def redis_key_prefix():
    """生成唯一的 Redis 键前缀，用于测试隔离"""
    return f"test:{uuid.uuid4().hex}:"


@pytest_asyncio.fixture
async def redis_cleanup(redis_client, redis_key_prefix):
    """
    Redis 测试数据清理 fixture。

    测试完成后自动清理带有前缀的键。
    """
    yield redis_key_prefix

    # 清理测试数据
    keys = await redis_client.keys(f"{redis_key_prefix}*")
    if keys:
        for key in keys:
            await redis_client.delete(key)


# =============================================================================
# MinIO Fixtures（function 级别）
# =============================================================================


@pytest_asyncio.fixture
async def minio_client(integration_settings, minio_available):
    """
    MinIO 客户端 fixture（function 作用域）。

    每个测试获取独立的客户端实例，避免事件循环冲突。
    """
    if not minio_available:
        pytest.skip("MinIO 服务不可用")

    from framework.storage.impl.minio import MinioStorage

    storage = MinioStorage(integration_settings.oss.minio)

    yield storage


@pytest.fixture
def minio_test_bucket():
    """生成唯一的测试存储桶名称"""
    return f"test-{uuid.uuid4().hex[:12]}"


@pytest_asyncio.fixture
async def minio_cleanup(minio_client, minio_test_bucket):
    """
    MinIO 测试数据清理 fixture。

    测试完成后自动清理测试存储桶。
    """
    # 确保测试存储桶存在
    await minio_client.create_bucket(minio_test_bucket)

    yield minio_test_bucket

    # 清理测试存储桶中的对象
    try:
        objects = await minio_client.list_objects(minio_test_bucket)
        for obj in objects:
            await minio_client.delete(minio_test_bucket, obj)
    except Exception:
        pass


# =============================================================================
# 初始化 Redis 连接（用于需要手动初始化的场景）
# =============================================================================


@pytest_asyncio.fixture
async def init_redis(integration_settings, redis_available):
    """
    初始化 Redis 连接（function 级别）。

    用于需要手动管理 Redis 连接的测试。
    """
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    # 如果已初始化，先关闭
    if RedisUtil.is_initialized():
        try:
            await RedisUtil.close()
        except Exception:
            pass

    await RedisUtil.init(integration_settings.redis)

    yield

    # 安全关闭连接
    try:
        await RedisUtil.close()
    except Exception:
        pass


# =============================================================================
# 工具函数
# =============================================================================


def unique_id() -> str:
    """生成唯一 ID"""
    return uuid.uuid4().hex


async def wait_for_condition(condition, timeout: float = 5.0, interval: float = 0.1):
    """
    等待条件满足。

    Args:
        condition: 异步条件函数
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
    """
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if await condition():
            return True
        await asyncio.sleep(interval)
    return False


# =============================================================================
# Mock Session Fixture（单元测试使用）
# =============================================================================


@pytest_asyncio.fixture
def mock_session():
    """
    模拟数据库会话（单元测试使用）。

    提供 AsyncMock 的数据库会话。
    """
    from unittest.mock import AsyncMock, MagicMock

    from sqlalchemy.ext.asyncio import AsyncSession

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.scalar_one_or_none = AsyncMock()
    mock_session.scalars = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.delete = AsyncMock()
    return mock_session
