"""
任务调度器入口
"""

import asyncio
import signal

import click
from loguru import logger

from demo.tasks.setup import setup_scheduler, cleanup_scheduler

_logger = logger.bind(name=__name__)


async def run_task() -> None:
    """启动任务调度器"""
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda: stop.set_result(None)
        )

    try:
        await setup_scheduler()
        _logger.info("任务调度器已启动，等待调度...")
        await stop
    finally:
        await cleanup_scheduler()
        _logger.info("任务调度器已停止")


@click.command()
def main():
    """启动任务调度器"""
    asyncio.run(run_task())


if __name__ == "__main__":
    main()
