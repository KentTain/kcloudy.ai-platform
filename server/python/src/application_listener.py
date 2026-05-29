"""
消息监听器入口

通过动态模块扫描与装配启动消息监听器。
"""

import asyncio
import signal
from pathlib import Path

import click
from loguru import logger

from framework.module import load_modules, get_registry, ModuleDescriptor

_logger = logger.bind(name=__name__)


async def run_listener(module_names: list[str] | None = None) -> None:
    """
    启动消息监听器

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
        loop.add_signal_handler(
            sig, lambda: stop.set_result(None)
        )

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
    try:
        from framework.tenant.protocols import register_tenant_provider
        from iam.services.tenant_provider_impl import iam_tenant_provider
        register_tenant_provider(iam_tenant_provider)
    except ImportError:
        _logger.warning("IAM TenantProvider 不可用")

    # 收集所有模块的监听器
    setup_funcs = []
    cleanup_funcs = []
    settings_obj = None

    try:
        from demo.configs import settings as demo_settings
        settings_obj = demo_settings
    except ImportError:
        from framework.configs import get_settings
        settings_obj = get_settings()

    registry = get_registry()
    for module in registry.get_all_modules():
        listener_setup = module.get_listener_setup()
        if listener_setup is not None:
            setup_func, cleanup_func = listener_setup
            setup_funcs.append((setup_func, module.name))
            cleanup_funcs.append((cleanup_func, module.name))
            _logger.info(f"注册监听器: {module.name}")

    try:
        for setup_func, module_name in setup_funcs:
            try:
                await setup_func(settings_obj)
                _logger.info(f"监听器已启动 [{module_name}]")
            except Exception:
                _logger.exception(f"监听器启动失败 [{module_name}]")

        _logger.info("所有监听器已启动，等待消息...")
        await stop
    finally:
        for cleanup_func, module_name in cleanup_funcs:
            try:
                await cleanup_func()
            except Exception:
                _logger.exception(f"监听器清理失败 [{module_name}]")
        _logger.info("所有监听器已停止")


@click.command()
@click.option("--module", default=None, help="指定加载的模块（逗号分隔）")
def main(module: str | None):
    """启动消息监听器"""
    module_names = module.split(",") if module else None
    asyncio.run(run_listener(module_names))


if __name__ == "__main__":
    main()