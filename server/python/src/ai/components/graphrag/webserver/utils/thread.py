"""提供图谱检索增强生成工具相关功能。"""

import asyncio
import logging
import platform

log = logging.getLogger(__name__)


def run_async(execute: asyncio.coroutines) -> None:
    """
    执行run_async。

    Args:
        execute (asyncio.coroutines): execute 参数。
    """
    if platform.system() == "Windows":
        import nest_asyncio  # type: ignore Ignoring because out of windows this will cause an error

        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(execute())
    else:
        import uvloop  # type: ignore Ignoring because on windows this will cause an error

        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:  # type: ignore Ignoring because minor versions this will throw an error
            runner.run(execute())
