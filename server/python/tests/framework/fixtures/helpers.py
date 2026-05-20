"""
Framework 模块测试辅助函数

提供测试通用的辅助函数和工具。
"""

import asyncio
import uuid
from typing import Callable, Coroutine


def unique_id() -> str:
    """生成唯一 ID"""
    return uuid.uuid4().hex


async def wait_for_condition(
    condition: Callable[[], Coroutine],
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """
    等待条件满足

    Args:
        condition: 异步条件函数
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）

    Returns:
        条件是否在超时前满足
    """
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if await condition():
            return True
        await asyncio.sleep(interval)
    return False
