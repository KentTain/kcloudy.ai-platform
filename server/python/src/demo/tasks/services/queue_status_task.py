"""集群队列状态检查任务"""

from loguru import logger

from demo.listeners.services.queue.constants import DATASET_NOTIFY_QUEUE
from framework.configs import init_settings
from framework.queue import get_queue_provider

_logger = logger.bind(name=__name__)


async def queue_status_task() -> None:
    """检查队列长度并记录日志，每 5 分钟由调度器触发"""
    try:
        settings = init_settings()
        queue_provider = get_queue_provider(settings.messaging)
        length = await queue_provider.get_queue_length(DATASET_NOTIFY_QUEUE)
        _logger.info(f"queue_status => {DATASET_NOTIFY_QUEUE} 队列长度: {length}")
    except Exception:
        _logger.exception("queue_status_task 执行异常")


# 配置: 集群任务, interval 触发, 5 分钟间隔
# 注册: demo.tasks.setup -> cluster_tasks
