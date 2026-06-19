"""
插件监控系统
提供心跳检测、资源监控、健康检查等功能
"""

from datetime import datetime
from typing import Any

import psutil


class PluginStats:
    def __init__(self) -> None:
        self.startup_times = []
        self.invoke_times = []
        self.error_count = 0
        self.success_count = 0
        self.total_invokes = 0
        self.last_accessed: datetime | None = None
        self.memory_usage = []
        self.cpu_usage = []
        self.created_at = datetime.now()


class SystemStats:
    def __init__(self, total_memory_mb=0.0, cpu_count=0) -> None:
        self.total_memory_mb = total_memory_mb
        self.cpu_count = cpu_count


class PluginPerformanceMonitor:
    """插件性能监控器"""

    def __init__(self):
        self.plugin_stats: dict[str, PluginStats] = {}

        self.system_stats = SystemStats(
            total_memory_mb=psutil.virtual_memory().total / 1024 / 1024,
            cpu_count=psutil.cpu_count(),
        )

    def record_startup_time(self, plugin_id: str, startup_time: float):
        """记录插件启动时间"""
        stats = self.plugin_stats.get(plugin_id, PluginStats())

        stats.startup_times.append({"time": startup_time, "timestamp": datetime.now()})
        # 只保留最近10次记录
        if len(stats.startup_times) > 10:
            stats.startup_times = stats.startup_times[-10:]

    def record_invoke_time(
        self, plugin_id: str, invoke_time: float, success: bool = True
    ):
        """记录插件调用时间"""
        stats = self.plugin_stats.get(plugin_id, PluginStats())
        stats.invoke_times.append(
            {"time": invoke_time, "timestamp": datetime.now(), "success": success}
        )
        stats.total_invokes += 1
        stats.last_accessed = datetime.now()

        if success:
            stats.success_count += 1
        else:
            stats.error_count += 1

        # 只保留最近100次记录
        if len(stats.invoke_times) > 100:
            stats.invoke_times = stats.invoke_times[-100:]

    def record_resource_usage(
        self, plugin_id: str, memory_mb: float, cpu_percent: float
    ):
        """记录资源使用情况"""
        stats = self.plugin_stats.get(plugin_id, PluginStats())
        stats.memory_usage.append({"memory_mb": memory_mb, "timestamp": datetime.now()})
        stats.cpu_usage.append(
            {"cpu_percent": cpu_percent, "timestamp": datetime.now()}
        )

        # 只保留最近50次记录
        if len(stats.memory_usage) > 50:
            stats.memory_usage = stats.memory_usage[-50:]
        if len(stats.cpu_usage) > 50:
            stats.cpu_usage = stats.cpu_usage[-50:]

    def get_plugin_metrics(self, plugin_id: str) -> dict[str, Any]:
        """获取插件性能指标"""
        if plugin_id not in self.plugin_stats:
            return {}

        stats = self.plugin_stats.get(plugin_id, PluginStats())

        # 计算平均启动时间
        avg_startup_time = 0
        if stats.startup_times:
            avg_startup_time = sum(s.time for s in stats.startup_times) / len(
                stats.startup_times
            )

        # 计算平均调用时间
        avg_invoke_time = 0
        success_rate = 0
        if stats.invoke_times:
            avg_invoke_time = sum(s.time for s in stats.invoke_times) / len(
                stats.invoke_times
            )
            success_rate = stats.success_count / stats.total_invokes * 100

        # 计算平均资源使用
        avg_memory = 0
        avg_cpu = 0
        if stats.memory_usage:
            avg_memory = sum(m.memory_mb for m in stats.memory_usage) / len(
                stats.memory_usage
            )
        if stats.cpu_usage:
            avg_cpu = sum(c.cpu_percent for c in stats.cpu_usage) / len(stats.cpu_usage)

        return {
            "plugin_id": plugin_id,
            "avg_startup_time_ms": round(avg_startup_time * 1000, 2),
            "avg_invoke_time_ms": round(avg_invoke_time * 1000, 2),
            "total_invokes": stats.total_invokes,
            "success_count": stats.success_count,
            "error_count": stats.error_count,
            "success_rate_percent": round(success_rate, 2),
            "avg_memory_mb": round(avg_memory, 2),
            "avg_cpu_percent": round(avg_cpu, 2),
            "last_accessed": stats.last_accessed,
            "created_at": stats.created_at,
            "recent_startup_times": stats.startup_times[-5:],
            "recent_invoke_times": stats.invoke_times[-10:],
        }

    def get_system_overview(self) -> dict[str, Any]:
        """获取系统总览"""
        total_plugins = len(self.plugin_stats)
        total_invokes = sum(stats.total_invokes for stats in self.plugin_stats.values())
        total_errors = sum(stats.error_count for stats in self.plugin_stats.values())

        # 获取当前系统资源使用
        current_memory = psutil.virtual_memory()
        current_cpu = psutil.cpu_percent(interval=1)

        return {
            "total_plugins": total_plugins,
            "total_invokes": total_invokes,
            "total_errors": total_errors,
            "system_memory_total_mb": round(self.system_stats.total_memory_mb, 2),
            "system_memory_used_mb": round(current_memory.used / 1024 / 1024, 2),
            "system_memory_percent": round(current_memory.percent, 2),
            "system_cpu_percent": current_cpu,
            "cpu_count": self.system_stats.cpu_count,
            "timestamp": datetime.now(),
        }
