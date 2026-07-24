"""document 模块定时任务注册"""


async def setup_tasks() -> None:
    """注册定时任务（索引恢复补偿、回收站自动清理）"""
    # TODO: 接入 framework scheduler
    pass


async def cleanup_tasks() -> None:
    """清理定时任务"""
    pass