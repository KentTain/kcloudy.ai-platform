"""
E2E 测试配置

提供 E2E 测试的 fixtures 和配置。

E2E 测试特性：
- 使用真实基础设施（数据库、Redis、MinIO）
- 创建隔离的测试租户和资源
- 测试完整的用户场景

运行方式：
    # 运行所有 E2E 测试
    uv run pytest -m e2e tests/ai/e2e/

注意：
    E2E 测试默认跳过，需显式指定 -m e2e 才运行
"""

import os
import sys
import time
from pathlib import Path
from typing import Callable

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# 设置测试环境
os.environ["PYTHON_SERVICE_ENV"] = "local"
os.environ["TZ"] = "Asia/Shanghai"

# =============================================================================
# Windows 事件循环策略修复
# =============================================================================
if sys.platform == "win32":
    if hasattr(__import__('asyncio'), 'WindowsSelectorEventLoopPolicy'):
        __import__('asyncio').set_event_loop_policy(
            __import__('asyncio').WindowsSelectorEventLoopPolicy()
        )


# =============================================================================
# pytest 标记配置
# =============================================================================


def pytest_configure(config):
    """
    注册自定义 pytest 标记。

    配置 E2E 测试标记，默认跳过 E2E 测试。
    """
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test (deselected by default, run with -m e2e)"
    )


def pytest_collection_modifyitems(config, items):
    """
    默认跳过 E2E 测试。

    只有显式指定 -m e2e 时才运行 E2E 测试。
    """
    # 检查是否显式选择了 e2e 标记
    e2e_selected = config.getoption("-m", default="") == "e2e"

    if not e2e_selected:
        skip_e2e = pytest.mark.skip(reason="E2E tests are skipped by default. Use -m e2e to run.")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)


# =============================================================================
# 配置加载
# =============================================================================

@pytest.fixture(scope="session")
def e2e_settings():
    """加载 E2E 测试配置"""
    from framework.configs import init_settings

    # conftest.py 在 server/python/tests/ai/e2e/
    # 配置在 server/config/
    # 路径: conftest.py -> e2e -> ai -> tests -> python -> server
    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
    settings = init_settings(config_dir)
    return settings


# =============================================================================
# 服务可用性检测
# =============================================================================

def _check_postgres_available(settings):
    """同步检测 PostgreSQL 服务是否可用"""
    import socket
    try:
        url = settings.sqlalchemy.url
        # postgresql+asyncpg://admin:password@host:port/database
        parts = url.split('@')[1].split('/')[0].split(':')
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5432

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _check_redis_available(settings):
    """同步检测 Redis 服务是否可用"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((
            settings.redis.single.host,
            settings.redis.single.port
        ))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_available(e2e_settings):
    """检测 PostgreSQL 服务是否可用"""
    return _check_postgres_available(e2e_settings)


@pytest.fixture(scope="session")
def redis_available(e2e_settings):
    """检测 Redis 服务是否可用"""
    return _check_redis_available(e2e_settings)


# =============================================================================
# 测试租户夹具
# =============================================================================

@pytest.fixture
def test_tenant_id():
    """
    生成唯一测试租户 ID。

    格式: e2e-test-{timestamp}

    用于创建隔离的测试环境，确保不同测试之间不会相互干扰。

    Returns:
        str: 唯一的测试租户 ID

    Example:
        >>> test_tenant_id = test_tenant_id()
        >>> print(test_tenant_id)
        'e2e-test-1719400000'
    """
    timestamp = int(time.time())
    return f"e2e-test-{timestamp}"


@pytest_asyncio.fixture
async def cleanup_test_resources(e2e_settings, test_tenant_id, redis_available):
    """
    清理测试资源的 fixture。

    在测试完成后自动清理：
    - 测试租户的所有数据库数据
    - Redis 中测试相关的 Key
    - OSS 中测试上传的文件

    使用方式：
        async def test_example(cleanup_test_resources):
            tenant_id = cleanup_test_resources["tenant_id"]
            # 测试结束后自动清理

    Returns:
        dict: 包含租户 ID 和清理标志的字典
    """
    yield {
        "tenant_id": test_tenant_id,
        "cleanup_done": False,
    }

    # =========================================================================
    # 清理逻辑
    # =========================================================================

    errors = []

    # -------------------------------------------------------------------------
    # 清理 Redis 中测试相关的 Key
    # -------------------------------------------------------------------------
    if redis_available:
        try:
            from framework.cache.redis_util import RedisUtil

            # 初始化 Redis 连接
            if not RedisUtil.is_initialized():
                await RedisUtil.init(e2e_settings.redis)

            # 查找并删除测试租户相关的 Key
            # Key 模式: tenant:{tenant_id}:* 或 test:{tenant_id}:*
            patterns = [
                f"tenant:{test_tenant_id}:*",
                f"test:{test_tenant_id}:*",
                f"e2e-test-{test_tenant_id}:*",
            ]

            for pattern in patterns:
                try:
                    keys = await RedisUtil.keys(pattern)
                    if keys:
                        for key in keys:
                            await RedisUtil.delete(key)
                except Exception as e:
                    errors.append(f"Redis 清理失败 (pattern={pattern}): {e}")

            # 关闭连接
            try:
                await RedisUtil.close()
            except Exception:
                pass

        except Exception as e:
            errors.append(f"Redis 连接失败: {e}")

    # -------------------------------------------------------------------------
    # 清理 OSS 中测试上传的文件
    # -------------------------------------------------------------------------
    try:
        from framework.storage.impl.minio import MinioStorage

        storage = MinioStorage(e2e_settings.oss.minio)

        # 获取默认 bucket
        bucket = e2e_settings.oss.minio.bucket or "default"

        # 列出并删除测试租户目录下的所有文件
        # 路径模式: {tenant_id}/* 或 test/{tenant_id}/*
        prefixes = [
            f"{test_tenant_id}/",
            f"test/{test_tenant_id}/",
        ]

        for prefix in prefixes:
            try:
                objects = await storage.list_objects(bucket, prefix=prefix)
                for obj in objects:
                    try:
                        await storage.delete(bucket, obj)
                    except Exception as e:
                        errors.append(f"OSS 删除失败 (object={obj}): {e}")
            except Exception as e:
                # 忽略 bucket 不存在等错误
                if "NoSuchBucket" not in str(e):
                    errors.append(f"OSS 列出对象失败 (prefix={prefix}): {e}")

    except Exception as e:
        # OSS 服务不可用，忽略
        if "Connection" not in str(e) and "connect" not in str(e).lower():
            errors.append(f"OSS 连接失败: {e}")

    # -------------------------------------------------------------------------
    # 清理测试租户的数据库数据
    # -------------------------------------------------------------------------
    # 注意：由于 E2E 测试使用独立的数据库会话，这里不自动清理数据库数据
    # 数据库清理应在具体的测试用例中根据业务逻辑处理
    # 例如：删除创建的租户记录、用户记录等

    if errors:
        import logging
        logger = logging.getLogger(__name__)
        for error in errors:
            logger.warning(f"测试资源清理警告: {error}")


# =============================================================================
# 数据库会话夹具
# =============================================================================

@pytest_asyncio.fixture
async def e2e_engine(e2e_settings, postgres_available):
    """
    E2E 测试数据库引擎。

    使用 NullPool 避免连接池问题，每次测试使用独立连接。
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        e2e_settings.sqlalchemy.url,
        echo=e2e_settings.sqlalchemy.echo,
        poolclass=NullPool,
    )

    yield engine

    # 安全清理
    try:
        await engine.dispose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def e2e_session(e2e_engine):
    """
    E2E 测试数据库会话。

    特性：
    - 支持独立事务
    - 自动回滚（测试结束后不污染数据库）

    使用方式：
        async def test_example(e2e_session):
            # 在事务中执行操作
            result = await e2e_session.execute(text("SELECT 1"))
            # 测试结束后自动回滚，不会影响数据库

    注意：
        由于 E2E 测试通常需要验证完整的业务流程，
        此 fixture 不会自动创建或清理测试租户。
        如果需要测试租户，请使用 test_tenant_id fixture 并手动创建。
    """
    # 创建会话
    session = AsyncSession(bind=e2e_engine, expire_on_commit=False)
    try:
        yield session
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass  # 忽略回滚错误
        raise
    finally:
        # 安全关闭会话，处理事件循环已关闭的情况
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            if not loop.is_closed():
                await session.rollback()
                await session.close()
        except RuntimeError:
            pass  # 事件循环已关闭，忽略


# =============================================================================
# 插件包路径夹具
# =============================================================================

# 插件包基础路径（相对于 server/python 目录）
_PLUGINS_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "plugins"

# 插件 ID 到文件名的映射
_PLUGIN_ID_TO_FILENAME = {
    "tongyi": "langgenius-tongyi_0.2.0.zip",
    "gpustack": "langgenius-gpustack_0.0.15.zip",
    "ollama": "langgenius-ollama_1.0.0.zip",
    "openai": "langgenius-openai_0.4.2.zip",
    "openai_api_compatible": "langgenius-openai_api_compatible_0.0.53.zip",
    "siliconflow": "langgenius-siliconflow_0.0.56.zip",
    "vllm": "yangyaofei-vllm_0.2.3.zip",
    "mineru-tianshu": "zyileven-mineru-tianshu_0.2.1.zip",
}


@pytest.fixture
def plugin_package_path() -> Callable[[str | None], Path]:
    """
    获取插件包路径。

    支持获取 `server/plugins/` 目录下真实插件包的绝对路径。

    Args:
        plugin_id: 插件 ID（如 "tongyi"、"gpustack"），为 None 时返回插件目录路径

    Returns:
        Path: 插件包的绝对路径

    Raises:
        ValueError: 插件 ID 不存在或插件包文件不存在

    Example:
        >>> get_path = plugin_package_path()
        >>> # 获取所有插件目录
        >>> plugins_dir = get_path(None)
        >>> print(plugins_dir)
        '/workspace/.../server/plugins'

        >>> # 获取指定插件包路径
        >>> tongyi_path = get_path("tongyi")
        >>> print(tongyi_path)
        '/workspace/.../server/plugins/langgenius-tongyi_0.2.0.zip'
    """
    def _get_plugin_path(plugin_id: str | None = None) -> Path:
        if plugin_id is None:
            # 返回插件目录路径
            if not _PLUGINS_BASE_DIR.exists():
                raise ValueError(f"插件目录不存在: {_PLUGINS_BASE_DIR}")
            return _PLUGINS_BASE_DIR

        # 获取指定插件包路径
        if plugin_id not in _PLUGIN_ID_TO_FILENAME:
            available = list(_PLUGIN_ID_TO_FILENAME.keys())
            raise ValueError(f"未知插件 ID: {plugin_id}。可用插件: {available}")

        filename = _PLUGIN_ID_TO_FILENAME[plugin_id]
        plugin_path = _PLUGINS_BASE_DIR / filename

        if not plugin_path.exists():
            raise ValueError(f"插件包文件不存在: {plugin_path}")

        return plugin_path

    return _get_plugin_path


# =============================================================================
# 辅助夹具
# =============================================================================

@pytest_asyncio.fixture
async def init_redis(e2e_settings, redis_available):
    """初始化 Redis 连接（function 级别）"""
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    # 如果已初始化，先关闭
    if RedisUtil.is_initialized():
        try:
            await RedisUtil.close()
        except Exception:
            pass

    await RedisUtil.init(e2e_settings.redis)

    yield

    # 安全关闭连接
    try:
        await RedisUtil.close()
    except Exception:
        pass


@pytest.fixture
def e2e_test_context(test_tenant_id):
    """
    E2E 测试上下文。

    提供测试所需的上下文信息，包括租户 ID 等。

    Returns:
        dict: 包含测试上下文信息的字典
    """
    return {
        "tenant_id": test_tenant_id,
        "test_run_id": f"run-{int(time.time())}",
    }


# =============================================================================
# API Key 夹具
# =============================================================================

@pytest.fixture
def tongyi_api_key():
    """
    获取通义千问 API Key。

    从环境变量 E2E_TONGYI_API_KEY 读取，如果未配置则跳过测试。

    Returns:
        str: 通义千问 API Key

    Raises:
        pytest.skip: 如果未配置环境变量
    """
    api_key = os.environ.get("E2E_TONGYI_API_KEY")
    if not api_key:
        pytest.skip("未配置 E2E_TONGYI_API_KEY 环境变量，跳过通义千问测试")
    return api_key


@pytest.fixture
def gpustack_api_key():
    """
    获取 GPUStack API Key。

    从环境变量 E2E_GPUSTACK_API_KEY 读取，如果未配置则跳过测试。

    Returns:
        str: GPUStack API Key

    Raises:
        pytest.skip: 如果未配置环境变量
    """
    api_key = os.environ.get("E2E_GPUSTACK_API_KEY")
    if not api_key:
        pytest.skip("未配置 E2E_GPUSTACK_API_KEY 环境变量，跳过 GPUStack 测试")
    return api_key
