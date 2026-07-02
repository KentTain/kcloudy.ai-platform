"""
E2E 测试配置

提供 E2E 测试特有的 fixtures：
- pytest 标记配置（默认跳过 e2e）
- Windows 事件循环策略（ProactorEventLoop，支持子进程）
- 服务可用性检测
- 数据库引擎和会话（NullPool）
- 资源清理
- 插件包路径
- 插件运行时环境
- Provider 注册

共享 fixtures（settings、tenant_id、API Key 等）来自上层 ai/conftest.py

运行方式：
    uv run pytest -m e2e tests/ai/e2e/

注意：
    E2E 测试默认跳过，需显式指定 -m e2e 才运行
"""

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# =============================================================================
# Windows 事件循环策略修复
# E2E 测试需要 ProactorEventLoop 支持子进程创建（如 uv 命令）
# =============================================================================
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# =============================================================================
# pytest 标记配置
# =============================================================================


def pytest_configure(config):
    """注册自定义 pytest 标记，默认跳过 E2E 测试。"""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test (deselected by default, run with -m e2e)",
    )


def pytest_collection_modifyitems(config, items):
    """默认跳过 E2E 测试，只有显式指定 -m e2e 时才运行。"""
    e2e_selected = config.getoption("-m", default="") == "e2e"

    if not e2e_selected:
        skip_e2e = pytest.mark.skip(
            reason="E2E tests are skipped by default. Use -m e2e to run."
        )
        for item in items:
            if item.get_closest_marker("e2e") is not None:
                item.add_marker(skip_e2e)


# =============================================================================
# E2E 测试租户（覆盖上层的 test_tenant_id，使用 e2e- 前缀）
# =============================================================================


@pytest.fixture
def test_tenant_id():
    """
    生成唯一 E2E 测试租户 ID。

    格式: e2e-test-{uuid8}
    """
    return "e2e-test-" + uuid.uuid4().hex[:8]


# =============================================================================
# 数据库会话夹具
# =============================================================================


@pytest_asyncio.fixture
async def e2e_engine(ai_settings, postgres_available):
    """E2E 测试数据库引擎（NullPool）"""
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        ai_settings.sqlalchemy.url,
        echo=ai_settings.sqlalchemy.echo,
        poolclass=NullPool,
    )

    yield engine

    try:
        await engine.dispose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def e2e_session(e2e_engine):
    """E2E 测试数据库会话"""
    session = AsyncSession(bind=e2e_engine, expire_on_commit=False)
    try:
        yield session
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            loop = asyncio.get_running_loop()
            if not loop.is_closed():
                await session.rollback()
                await session.close()
        except RuntimeError:
            pass


# =============================================================================
# 资源清理
# =============================================================================


@pytest_asyncio.fixture
async def cleanup_test_resources(ai_settings, test_tenant_id, redis_available):
    """
    清理测试资源的 fixture。

    在测试完成后自动清理 Redis Key、OSS 文件等。
    """
    yield {
        "tenant_id": test_tenant_id,
        "cleanup_done": False,
    }

    errors = []

    # 清理 Redis
    if redis_available:
        try:
            from framework.cache.redis_util import RedisUtil

            if not RedisUtil.is_initialized():
                await RedisUtil.init(ai_settings.redis)

            patterns = [
                f"tenant:{test_tenant_id}:*",
                f"test:{test_tenant_id}:*",
                f"{test_tenant_id}:*",
            ]

            for pattern in patterns:
                try:
                    keys = await RedisUtil.keys(pattern)
                    if keys:
                        for key in keys:
                            await RedisUtil.delete(key)
                except Exception as e:
                    errors.append(f"Redis 清理失败 (pattern={pattern}): {e}")

            try:
                await RedisUtil.close()
            except Exception:
                pass

        except Exception as e:
            errors.append(f"Redis 连接失败: {e}")

    # 清理 OSS
    try:
        from framework.storage.impl.minio import MinioStorage

        storage = MinioStorage(ai_settings.oss.minio)
        bucket = ai_settings.oss.minio.bucket or ai_settings.oss.bucket

        # 检查桶是否存在
        import socket
        try:
            endpoint = ai_settings.oss.minio.endpoint
            host = endpoint.split(":")[0]
            port = int(endpoint.split(":")[1]) if ":" in endpoint else 9000
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((host, port)) != 0:
                sock.close()
                raise ConnectionError("MinIO 不可用")
            sock.close()
        except Exception:
            raise ConnectionError("MinIO 不可用")

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
                if "NoSuchBucket" not in str(e):
                    errors.append(f"OSS 列出对象失败 (prefix={prefix}): {e}")

    except ConnectionError:
        pass  # MinIO 不可用，跳过清理
    except Exception as e:
        if "Connection" not in str(e) and "connect" not in str(e).lower():
            errors.append(f"OSS 连接失败: {e}")

    if errors:
        import logging

        logger = logging.getLogger(__name__)
        for error in errors:
            logger.warning(f"测试资源清理警告: {error}")


# =============================================================================
# 插件包路径夹具
# =============================================================================

_PLUGINS_BASE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "plugins"
)

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

    Args:
        plugin_id: 插件 ID（如 "tongyi"、"gpustack"），为 None 时返回插件目录路径

    Returns:
        Path: 插件包的绝对路径
    """

    def _get_plugin_path(plugin_id: str | None = None) -> Path:
        if plugin_id is None:
            if not _PLUGINS_BASE_DIR.exists():
                raise ValueError(f"插件目录不存在: {_PLUGINS_BASE_DIR}")
            return _PLUGINS_BASE_DIR

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


@pytest.fixture
def e2e_test_context(test_tenant_id):
    """E2E 测试上下文"""
    return {
        "tenant_id": test_tenant_id,
        "test_run_id": f"run-{int(time.time())}",
    }


# =============================================================================
# 插件测试夹具
# =============================================================================


@pytest_asyncio.fixture
async def plugin_provider():
    """
    注册 PluginInstallationProvider。

    同时初始化数据库引擎池并运行必要的迁移。
    """
    from framework.configs.settings import get_settings

    try:
        settings = get_settings()
    except RuntimeError:
        config_dir = (
            Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
        )
        from framework.configs import init_settings

        settings = init_settings(config_dir)

    from framework.database.core.engine_pool import init_default_engine

    init_default_engine(
        database_url=settings.sqlalchemy.url,
        echo=settings.sqlalchemy.echo,
    )

    from alembic import command
    from alembic.config import Config

    src_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "src"

    for module_name in ("tenant", "ai"):
        module_dir = src_path / module_name / "migrations"
        if module_dir.exists() and (module_dir / "versions").exists():
            try:
                alembic_cfg = Config()
                alembic_cfg.set_main_option("script_location", str(module_dir))
                alembic_cfg.set_main_option(
                    "version_locations", str(module_dir / "versions")
                )
                alembic_cfg.set_main_option(
                    "sqlalchemy.url", str(settings.sqlalchemy.url)
                )
                command.upgrade(alembic_cfg, "head")
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(
                    f"模块 {module_name} 迁移执行异常: {e}"
                )

    from framework.tenant.plugin_protocols import (
        get_plugin_installation_provider,
        register_plugin_installation_provider,
    )

    try:
        get_plugin_installation_provider()
    except RuntimeError:
        from tenant.services.plugin_provider import (
            plugin_installation_provider_impl,
        )

        register_plugin_installation_provider(plugin_installation_provider_impl)

    yield get_plugin_installation_provider()

    from framework.database.core.engine_pool import get_engine_pool

    pool = get_engine_pool()
    await pool.close()


@pytest_asyncio.fixture
async def plugin_runtime_setup(
    test_tenant_id: str,
    plugin_package_path: callable,
    tmp_path: Path,
):
    """
    设置插件运行时测试环境。

    创建插件的完整工作目录：
    1. 解压插件包到工作目录
    2. 创建 Python 虚拟环境
    3. 解析插件配置并创建 PluginInfo
    4. 创建 LocalPluginRuntime 实例
    5. 执行 prepare

    返回:
        tuple: (manager, local_runtime, cleanup_func)
    """
    import json
    import shutil
    import subprocess
    import sys
    import zipfile
    from pathlib import Path

    from ai.components.plugin.engine.core.helper import PluginConfigProcessor
    from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory
    from ai.components.plugin.engine.core.runtime.local_runtime import (
        LocalPluginRuntime,
    )
    from ai.components.plugin.engine.models.plugin import PluginInfo

    plugin_id = "langgenius/tongyi"
    workspace_dir = (
        tmp_path / "plugins" / "tenants" / test_tenant_id / "runtime" / plugin_id
    )

    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    package_path: Path = plugin_package_path("tongyi")
    with zipfile.ZipFile(package_path, "r") as zf:
        zf.extractall(workspace_dir)

    (workspace_dir / "config").mkdir(parents=True, exist_ok=True)

    venv_path = workspace_dir / ".venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        check=True,
        capture_output=True,
    )
    python_interpreter = str(venv_path / "bin" / "python")

    processor = PluginConfigProcessor(plugin_dir=workspace_dir)
    processor.parse_plugin_config()
    plugin_config = processor.get_plugin_config()

    plugin_info = PluginInfo(installed_at=datetime.now())
    object.__setattr__(plugin_info, "config", plugin_config)

    from sqlalchemy.ext.asyncio import AsyncSession

    from framework.database.dependencies import get_db_session

    runtime = LocalPluginRuntime(plugin_info=plugin_info, workspace_dir=workspace_dir)
    runtime.virtual_env_path = venv_path
    runtime.python_interpreter_path = python_interpreter

    uv_path = shutil.which("uv")
    if uv_path:
        runtime.uv_path = uv_path
    else:
        runtime.uv_path = None

    marker_file = workspace_dir / ".prepared"
    marker_file.write_text(
        f"prepared_at: {datetime.now().isoformat()}\n"
        f"plugin_name: {plugin_info.name}\n"
        f"plugin_version: {plugin_info.version}\n"
    )

    manifest = {
        "plugin_info": {
            "name": plugin_info.name or plugin_config.configuration.name,
            "version": plugin_info.version or plugin_config.configuration.version,
            "author": plugin_config.configuration.author,
        },
        "preparation_info": {
            "prepared_at": datetime.now().isoformat(),
            "workspace_dir": str(workspace_dir),
            "virtual_env_path": str(venv_path),
            "python_interpreter": python_interpreter,
        },
        "environment_info": {},
        "runtime_config": {
            "entrypoint": "main",
            "language": "python",
            "memory_limit": None,
        },
    }
    with open(workspace_dir / "config" / "runtime_manifest.json", "w") as f:
        json.dump(manifest, f)

    runtime._is_prepared = True
    runtime._state = "prepared"
    runtime._is_running = False
    runtime.prepared_at = datetime.now()
    runtime.environment_info = {
        "uv_path": uv_path,
        "python_interpreter": python_interpreter,
    }

    async def _mock_start_plugin_process(self):
        """创建简单的长时间运行的测试 Python 进程"""
        import asyncio

        worker_script = self.workspace_dir / "test_worker.py"
        worker_script.write_text(
            "import signal, time\n"
            "signal.signal(signal.SIGTERM, lambda *_: exit(0))\n"
            "print('WORKER_READY')\n"
            "import sys; sys.stdout.flush()\n"
            "while True:\n"
            "    time.sleep(1)\n"
        )

        cmd = [self.python_interpreter_path, str(worker_script)]
        self._plugin_logger.info(f"测试启动命令: {' '.join(cmd)}")

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.workspace_dir,
        )
        self.process_id = self.process.pid
        self._plugin_logger.info(f"测试进程启动成功: PID {self.process_id}")

        self._output_task = asyncio.create_task(self._handle_process_output())

    import types

    runtime._start_plugin_process = types.MethodType(
        _mock_start_plugin_process, runtime
    )

    async def cleanup():
        if runtime.is_running:
            try:
                await runtime.stop()
            except Exception:
                pass
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir, ignore_errors=True)

    yield runtime, cleanup

    await cleanup()


# =============================================================================
# Provider 注册夹具
# =============================================================================


@pytest.fixture
def registered_provider():
    """注册 PluginInstallationProvider"""
    from framework.tenant.plugin_protocols import (
        register_plugin_installation_provider,
    )
    from tenant.services.plugin_provider import plugin_installation_provider_impl

    register_plugin_installation_provider(plugin_installation_provider_impl)
    return plugin_installation_provider_impl
