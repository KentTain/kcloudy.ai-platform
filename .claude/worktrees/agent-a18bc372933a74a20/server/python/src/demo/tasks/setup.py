"""Tasks 生命周期管理——双调度器"""

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from demo.configs import settings
from demo.tasks.services.heartbeat_task import heartbeat_task
from demo.tasks.services.queue_status_task import queue_status_task

_logger = logger.bind(name=__name__)

_local_scheduler: AsyncIOScheduler | None = None
_cluster_scheduler: AsyncIOScheduler | None = None

# 声明式任务注册列表
# 本地任务: (func, task_id, trigger_args)
local_tasks = [
    (heartbeat_task, "demo_heartbeat_task", {"seconds": 60}),
]

# 集群任务: (func, task_id, trigger, trigger_args)
cluster_tasks = [
    (
        queue_status_task,
        "demo_queue_status_task",
        "interval",
        {"minutes": 5},
    ),
]


async def setup_scheduler() -> None:
    """注册并启动所有调度器"""
    global _local_scheduler, _cluster_scheduler

    # 本地调度器（使用默认 MemoryJobStore）
    _local_scheduler = AsyncIOScheduler(
        timezone="Asia/Shanghai",
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
    )

    for func, task_id, trigger_args in local_tasks:
        _local_scheduler.add_job(
            func,
            "interval",
            id=task_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            **trigger_args,
        )
    _local_scheduler.start()
    _logger.info(f"本地调度器已启动，共 {len(local_tasks)} 个任务")

    # 集群调度器
    try:
        # 使用 settings.redis 配置，而不是 messaging.connections
        redis_config = settings.redis
        jobstore = _create_redis_jobstore(redis_config)

        _cluster_scheduler = AsyncIOScheduler(
            jobstores={"default": jobstore},
            timezone="Asia/Shanghai",
            coalesce=True,
            max_instances=1,
            misfire_grace_time=60,
        )

        for func, task_id, trigger, trigger_args in cluster_tasks:
            _cluster_scheduler.add_job(
                func,
                trigger,
                id=task_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                **trigger_args,
            )
        _cluster_scheduler.start()
        _logger.info(f"集群调度器已启动，共 {len(cluster_tasks)} 个任务")
    except Exception:
        _logger.exception("集群调度器启动失败，跳过")
        _cluster_scheduler = None


async def cleanup_scheduler() -> None:
    """优雅停止所有调度器"""
    for scheduler in [_local_scheduler, _cluster_scheduler]:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=True)
    _logger.info("调度器已停止")


def _create_redis_jobstore(redis_config) -> RedisJobStore:
    """从配置创建 RedisJobStore

    Args:
        redis_config: RedisSettings 对象或 dict
    """
    # 支持 RedisSettings 对象和 dict
    if hasattr(redis_config, "single"):
        # RedisSettings 对象
        single = redis_config.single
        host = single.host
        port = single.port
        password = single.password or None
        db = single.db
    else:
        # dict 格式（向后兼容）
        host = redis_config.get("host", "localhost")
        port = redis_config.get("port", 6379)
        password = redis_config.get("password") or None
        db = redis_config.get("db", 0)

    return RedisJobStore(
        host=host,
        port=port,
        password=password,
        db=db,
    )
