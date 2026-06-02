import os

from loguru import logger


async def start_plugin_engine() -> None:
    """
    启动插件引擎
    """
    logger.info("启动插件引擎")

    if not os.environ.get("TIKTOKEN_CACHE_DIR"):
        from alon.core.common.path import WORKSPACE_ROOT_DIR

        cache_dir = os.path.join(WORKSPACE_ROOT_DIR, ".cache/tiktoken")
        logger.info(f"设置TIKTOKEN_CACHE_DIR: {cache_dir}")
        os.environ["TIKTOKEN_CACHE_DIR"] = cache_dir
    else:
        logger.info(f"TIKTOKEN_CACHE_DIR: {os.environ.get('TIKTOKEN_CACHE_DIR')}")

    # 启动时，尝试强制杀死之前异常退出的插件进程
    from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory

    await PluginManagerFactory.shutdown_all()


async def stop_plugin_engine() -> None:
    """
    停止插件引擎
    """
    logger.info("清理插件引擎进程")
    from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory

    await PluginManagerFactory.shutdown_all()
