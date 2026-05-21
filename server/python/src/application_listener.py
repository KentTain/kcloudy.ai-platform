"""
消息监听器入口
"""

import asyncio
import signal

import click
from loguru import logger

from demo.core.common.path import CONFIG_FOLDER
from demo.listeners.setup import setup_listeners, cleanup_listeners
from framework.configs import init_settings

_logger = logger.bind(name=__name__)


async def run_listener() -> None:
    """启动消息监听器"""
    settings = init_settings(CONFIG_FOLDER)

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda: stop.set_result(None)
        )

    try:
        await setup_listeners(settings)
        _logger.info("消息监听器已启动，等待消息...")
        await stop
    finally:
        await cleanup_listeners()
        _logger.info("消息监听器已停止")


@click.command()
def main():
    """启动消息监听器"""
    asyncio.run(run_listener())


if __name__ == "__main__":
    main()
