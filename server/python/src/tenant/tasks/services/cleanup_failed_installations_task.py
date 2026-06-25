"""定时清理 FAILED 状态安装记录"""
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import select

from framework.database.dependencies import get_task_session
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logger.bind(name=__name__)


async def cleanup_failed_installations_task() -> None:
    """
    清理超过 24 小时的 FAILED 状态安装记录

    设计文档（风险 1）：定时任务清理超过 24 小时的 FAILED 记录，
    避免孤儿记录累积。
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        async with get_task_session() as session:
            stmt = select(TenantPluginInstallation).where(
                TenantPluginInstallation.status == "FAILED",
                TenantPluginInstallation.created_at < cutoff,
            )
            result = await session.execute(stmt)
            records = result.scalars().all()

            if records:
                for record in records:
                    await record.delete(session)
                _logger.info(f"已清理 {len(records)} 条 FAILED 安装记录")
    except Exception:
        _logger.exception("清理 FAILED 安装记录异常")
