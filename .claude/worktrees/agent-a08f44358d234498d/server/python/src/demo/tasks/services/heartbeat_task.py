"""本地心跳定时任务"""

from datetime import datetime, timezone

from loguru import logger

_logger = logger.bind(name=__name__)


async def heartbeat_task() -> None:
    """记录心跳时间戳，每 60 秒由调度器触发"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        _logger.info(f"heartbeat => {now}")
    except Exception:
        _logger.exception("heartbeat_task 执行异常")


# 配置: 本地任务, interval 触发, 60 秒间隔
# 注册: demo.tasks.setup -> local_tasks
