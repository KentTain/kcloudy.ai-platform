"""Tasks 生命周期管理——本地调度器"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from tenant.tasks.services.cleanup_failed_installations_task import (
    cleanup_failed_installations_task,
)
from tenant.tasks.services.cleanup_pending_installations_task import (
    cleanup_pending_installations_task,
)

_logger = logger.bind(name=__name__)

_scheduler: AsyncIOScheduler | None = None

# 本地任务注册列表: (func, task_id, trigger_args)
local_tasks = [
    (
        cleanup_failed_installations_task,
        "tenant_cleanup_failed_installations",
        {"hours": 1},
    ),
    (
        cleanup_pending_installations_task,
        "tenant_cleanup_pending_installations",
        {"hours": 1},
    ),
]


async def setup_scheduler() -> None:
    """注册并启动本地调度器"""
    global _scheduler

    _scheduler = AsyncIOScheduler(
        timezone="Asia/Shanghai",
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
    )

    for func, task_id, trigger_args in local_tasks:
        _scheduler.add_job(
            func,
            "interval",
            id=task_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            **trigger_args,
        )
    _scheduler.start()
    _logger.info(f"Tenant 调度器已启动，共 {len(local_tasks)} 个任务")


async def cleanup_scheduler() -> None:
    """优雅停止调度器"""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
    _logger.info("Tenant 调度器已停止")
