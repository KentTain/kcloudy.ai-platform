"""
任务调度器入口

通过动态模块扫描与装配启动任务调度器。
"""

import asyncio
import signal
from pathlib import Path

import click
from loguru import logger

from framework.module import ModuleDescriptor, get_registry, load_modules
from framework.tenant.protocols import register_tenant_provider

_logger = logger.bind(name=__name__)


async def run_task(module_names: list[str] | None = None) -> None:
    """
    启动任务调度器

    Args:
        module_names: 要加载的模块名列表，None 表示加载全部
    """
    # 如果未指定模块，尝试从配置文件读取
    if module_names is None:
        try:
            from config.modules import ENABLED_MODULES

            module_names = ENABLED_MODULES
            _logger.info(f"Loaded modules from config: {ENABLED_MODULES}")
        except ImportError:
            _logger.info("No modules config found, loading all modules")

    # 加载模块
    src_path = Path(__file__).parent
    modules = load_modules(src_path, module_names)

    _logger.info(f"已加载模块: {[m.name for m in modules]}")

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop.set_result(None))

    # 初始化数据库引擎
    try:
        from demo.configs import settings
        from framework.database.core.engine import setup_engine

        sqlalchemy_config = settings.sqlalchemy
        setup_engine(
            database_url=sqlalchemy_config.url,
            echo=sqlalchemy_config.echo,
            pool_size=sqlalchemy_config.pool.size,
            max_overflow=sqlalchemy_config.pool.max_overflow,
        )
    except Exception:
        _logger.exception("数据库引擎初始化失败")

    # 注册 TenantProvider
    provider = _get_tenant_provider()
    if provider:
        register_tenant_provider(provider)

    # 收集所有模块的任务调度器
    setup_funcs = []
    cleanup_funcs = []

    registry = get_registry()
    for module in registry.get_all_modules():
        task_setup = module.get_task_setup()
        if task_setup is not None:
            setup_func, cleanup_func = task_setup
            setup_funcs.append(setup_func)
            cleanup_funcs.append(cleanup_func)
            _logger.info(f"注册任务调度器: {module.name}")

    try:
        for setup_func in setup_funcs:
            await setup_func()
        _logger.info("所有任务调度器已启动，等待调度...")
        await stop
    finally:
        for cleanup_func in cleanup_funcs:
            try:
                await cleanup_func()
            except Exception:
                _logger.exception("任务调度器清理失败")
        _logger.info("所有任务调度器已停止")


def _get_tenant_provider():
    """获取 TenantProvider 实现"""
    try:
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        return tenant_provider_impl
    except ImportError:
        _logger.warning("TenantProvider 不可用")
        return None


@click.command()
@click.option("--module", default=None, help="指定加载的模块（逗号分隔）")
def main(module: str | None):
    """启动任务调度器"""
    module_names = module.split(",") if module else None
    asyncio.run(run_task(module_names))


if __name__ == "__main__":
    main()
