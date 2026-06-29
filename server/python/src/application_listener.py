"""
消息监听器入口

通过动态模块扫描与装配启动消息监听器。
"""

import asyncio
import signal
from pathlib import Path

import click
from loguru import logger

from framework.module import get_registry, load_modules
from framework.tenant.tenant_protocols import register_tenant_provider
from framework.utils.log_util import write_info, write_warning
from framework.utils.startup_timer import StartupTimer

_logger = logger.bind(name=__name__)


async def run_listener(module_names: list[str] | None = None) -> None:
    """
    启动消息监听器

    Args:
        module_names: 要加载的模块名列表，None 表示加载全部
    """
    timer = StartupTimer(app_name="消息监听器")

    # 阶段1: 配置加载 (order=1)
    with timer.phase("配置加载", order=1):
        if module_names is None:
            try:
                from config.modules import ENABLED_MODULES

                module_names = ENABLED_MODULES
                write_info(f"Loaded modules from config: {ENABLED_MODULES}")
            except ImportError:
                write_info("No modules config found, loading all modules")

    # 阶段2: 基础组件初始化 (order=2)
    with timer.phase("基础组件初始化", order=2) as phase:
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
            phase.details["数据库"] = "PostgreSQL"
        except Exception:
            _logger.exception("数据库引擎初始化失败")

        # 初始化 Redis 客户端
        try:
            from framework.cache.redis_util import RedisUtil

            await RedisUtil.init(settings.redis)
            phase.details["Redis"] = "已初始化"
        except Exception:
            _logger.exception("Redis 客户端初始化失败")

        provider = _get_tenant_provider()
        if provider:
            register_tenant_provider(provider)
            phase.details["TenantProvider"] = "已注册"

    # 阶段3: 模块加载 (order=3)
    with timer.phase("模块加载", order=3):
        src_path = Path(__file__).parent
        modules = load_modules(src_path, module_names)
        write_info(f"已加载模块: {[m.name for m in modules]}")

    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop.set_result(None))

    # 阶段4: 监听器启动 (order=4)
    with timer.phase("监听器启动", order=4) as phase:
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
                write_info(f"注册监听器: {module.name}")

        started_count = 0
        for setup_func, module_name in setup_funcs:
            try:
                await setup_func(settings_obj)
                write_info(f"监听器已启动 [{module_name}]")
                started_count += 1
            except Exception:
                _logger.exception(f"监听器启动失败 [{module_name}]")

        phase.details["已启动监听器"] = f"{started_count} 个"

    # 输出启动摘要
    registry = get_registry()
    module_names_list = [m.name for m in registry.get_all_modules()]
    timer.print_summary(
        modules=module_names_list,
        extra_info={"状态": "监听器正在运行，等待消息..."},
    )

    try:
        await stop
    finally:
        for cleanup_func, module_name in cleanup_funcs:
            try:
                await cleanup_func()
            except Exception:
                _logger.exception(f"监听器清理失败 [{module_name}]")

        # 关闭 Redis 连接
        try:
            from framework.cache.redis_util import RedisUtil

            await RedisUtil.close()
        except Exception:
            _logger.exception("Redis 连接关闭失败")

        write_info("所有监听器已停止")


def _get_tenant_provider():
    """获取 TenantProvider 实现"""
    try:
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        return tenant_provider_impl
    except ImportError:
        write_warning("TenantProvider 不可用")
        return None


@click.command()
@click.option("--module", default=None, help="指定加载的模块（逗号分隔）")
def main(module: str | None):
    """启动消息监听器"""
    module_names = module.split(",") if module else None
    asyncio.run(run_listener(module_names))


if __name__ == "__main__":
    main()
