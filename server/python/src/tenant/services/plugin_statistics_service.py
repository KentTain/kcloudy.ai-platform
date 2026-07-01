"""
插件统计服务

提供插件定义和安装的统计数据查询。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation
from tenant.schemas.plugin import (
    DefinitionStats,
    InstallationStats,
    PluginStatisticsResponse,
)

_logger = logging.getLogger(__name__)


class PluginStatisticsService:
    """插件统计服务"""

    @staticmethod
    async def get_statistics(session: AsyncSession) -> PluginStatisticsResponse:
        """
        获取插件统计数据

        Args:
            session: 数据库会话

        Returns:
            PluginStatisticsResponse: 统计数据响应
        """
        # 1. 插件定义统计
        definition_stats = await PluginStatisticsService._get_definition_stats(session)

        # 2. 插件安装统计
        installation_stats = await PluginStatisticsService._get_installation_stats(session)

        return PluginStatisticsResponse(
            definition_stats=definition_stats,
            installation_stats=installation_stats,
            cached_at=None,  # 实时计算，无缓存
        )

    @staticmethod
    async def _get_definition_stats(session: AsyncSession) -> DefinitionStats:
        """
        获取插件定义统计数据

        Args:
            session: 数据库会话

        Returns:
            DefinitionStats: 插件定义统计
        """
        # 总数
        total_result = await session.execute(
            select(func.count(TenantPluginDefinition.id))
        )
        total_count = total_result.scalar() or 0

        # 按安装类型分布（过滤掉 None 值）
        type_result = await session.execute(
            select(
                TenantPluginDefinition.install_type,
                func.count(TenantPluginDefinition.id)
            )
            .group_by(TenantPluginDefinition.install_type)
        )
        # 将枚举值转换为字符串，过滤掉 None
        by_type = {}
        for row in type_result.all():
            if row[0] is not None:
                # 枚举值转换为字符串
                key = row[0].value if hasattr(row[0], 'value') else str(row[0])
                by_type[key] = row[1]

        # 推荐插件数
        recommended_result = await session.execute(
            select(func.count(TenantPluginDefinition.id))
            .where(TenantPluginDefinition.is_recommended == True)
        )
        recommended_count = recommended_result.scalar() or 0

        # 启用插件数
        enabled_result = await session.execute(
            select(func.count(TenantPluginDefinition.id))
            .where(TenantPluginDefinition.is_enabled == True)
        )
        enabled_count = enabled_result.scalar() or 0

        return DefinitionStats(
            total_count=total_count,
            by_type=by_type,
            recommended_count=recommended_count,
            enabled_count=enabled_count,
        )

    @staticmethod
    async def _get_installation_stats(session: AsyncSession) -> InstallationStats:
        """
        获取插件安装统计数据

        Args:
            session: 数据库会话

        Returns:
            InstallationStats: 插件安装统计
        """
        # 总安装数
        total_result = await session.execute(
            select(func.count(TenantPluginInstallation.id))
        )
        total_count = total_result.scalar() or 0

        # 活跃安装数（状态为 ACTIVE）
        active_result = await session.execute(
            select(func.count(TenantPluginInstallation.id))
            .where(TenantPluginInstallation.status == "ACTIVE")
        )
        active_count = active_result.scalar() or 0

        # 本周新增安装数（计算本周一开始的时间）
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        weekly_result = await session.execute(
            select(func.count(TenantPluginInstallation.id))
            .where(TenantPluginInstallation.created_at >= week_start)
        )
        weekly_new_count = weekly_result.scalar() or 0

        return InstallationStats(
            total_count=total_count,
            active_count=active_count,
            weekly_new_count=weekly_new_count,
        )


# 单例实例
plugin_statistics_service = PluginStatisticsService()
