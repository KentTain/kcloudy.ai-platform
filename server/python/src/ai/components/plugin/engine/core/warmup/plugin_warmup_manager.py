import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.plugin.engine.utils.logger import get_logger


logger = get_logger(__name__)


# 枚举类定义
class WarmupStatus(str, Enum):
    """预热状态枚举"""

    DISABLED = "disabled"
    NO_CANDIDATES = "no_candidates"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"


class PluginWarmupResult(str, Enum):
    """单个插件预热结果枚举"""

    SUCCESS = "success"
    FAILED = "failed"
    ALREADY_RUNNING = "already_running"
    ALREADY_WARMING = "already_warming"


# 数据对象定义
class WarmupConfig(BaseModel):
    """插件预热配置"""

    enabled: bool = Field(default=True, description="是否启用预热")
    max_warmup_plugins: int = Field(default=5, description="最多预热插件数量")
    min_usage_count: int = Field(default=3, description="最少使用次数才考虑预热")
    warmup_threshold_days: int = Field(default=7, description="基于最近几天的使用情况")
    auto_warmup_interval: int = Field(
        default=3600, description="自动预热检查间隔（秒）"
    )
    warmup_on_startup: bool = Field(default=True, description="启动时是否执行预热")


class PluginMetrics(BaseModel):
    """插件性能指标"""

    plugin_id: str = Field(description="插件ID")
    total_invokes: int = Field(default=0, description="总调用次数")
    last_accessed: datetime | None = Field(default=None, description="最后访问时间")
    avg_startup_time_ms: float = Field(default=0.0, description="平均启动时间（毫秒）")
    success_rate_percent: float = Field(default=0.0, description="成功率百分比")

    @classmethod
    def from_dict(cls, plugin_id: str, metrics_dict: dict[str, Any]) -> "PluginMetrics":
        """从字典创建 PluginMetrics 对象"""
        return cls(
            plugin_id=plugin_id,
            total_invokes=metrics_dict.get("total_invokes", 0),
            last_accessed=metrics_dict.get("last_accessed"),
            avg_startup_time_ms=metrics_dict.get("avg_startup_time_ms", 0.0),
            success_rate_percent=metrics_dict.get("success_rate_percent", 0.0),
        )


class PluginCandidate(BaseModel):
    """预热候选插件"""

    plugin_id: str = Field(description="插件ID")
    frequency_score: float = Field(description="频率评分")
    total_invokes: int = Field(description="总调用次数")
    avg_startup_time_ms: float = Field(description="平均启动时间（毫秒）")
    last_accessed: datetime | None = Field(description="最后访问时间")
    success_rate: float = Field(description="成功率")


class SinglePluginWarmupResult(BaseModel):
    """单个插件预热结果"""

    plugin_id: str = Field(description="插件ID")
    result: PluginWarmupResult = Field(description="预热结果")
    warmup_time_seconds: float | None = Field(
        default=None, description="预热耗时（秒）"
    )
    error_message: str | None = Field(default=None, description="错误信息")


class WarmupExecutionResult(BaseModel):
    """预热执行结果"""

    status: WarmupStatus = Field(description="执行状态")
    warmed_plugins: list[PluginCandidate] = Field(
        default_factory=list, description="成功预热的插件"
    )
    failed_plugins: list[PluginCandidate] = Field(
        default_factory=list, description="预热失败的插件"
    )
    warmup_time: datetime | None = Field(default=None, description="预热时间")
    total_candidates: int = Field(default=0, description="候选插件总数")
    execution_time_seconds: float | None = Field(
        default=None, description="执行耗时（秒）"
    )


class WarmupStatusInfo(BaseModel):
    """预热状态信息"""

    enabled: bool = Field(description="是否启用预热")
    warming_up_plugins: list[str] = Field(
        default_factory=list, description="正在预热的插件"
    )
    warmed_plugins: list[str] = Field(default_factory=list, description="已预热的插件")
    warmup_config: WarmupConfig = Field(description="预热配置")
    last_warmup_time: datetime | None = Field(default=None, description="最后预热时间")


class PluginWarmupManager:
    """插件预热管理器"""

    def __init__(self, plugin_manager, performance_monitor):
        self.plugin_manager = plugin_manager
        self.performance_monitor = performance_monitor
        self.logger = get_logger(f"warmup_manager_{plugin_manager.tenant_id}")

        # 预热配置
        self.warmup_config = WarmupConfig()

        # 预热状态
        self.warming_up_plugins: set[str] = set()  # 正在预热的插件
        self.warmed_plugins: set[str] = set()  # 已预热的插件
        self.last_warmup_time: datetime | None = None

    async def analyze_warmup_candidates(self) -> list[PluginCandidate]:
        """分析预热候选插件"""
        candidates = []

        # 获取所有插件的性能指标
        all_metrics = await self.plugin_manager.get_all_plugins_performance_metrics()

        current_time = datetime.now()
        cutoff_time = current_time - timedelta(
            days=self.warmup_config.warmup_threshold_days
        )

        for plugin_id, metrics_dict in all_metrics.items():
            # 跳过已在运行的插件
            if plugin_id in self.plugin_manager.running_plugins:
                continue

            # 跳过正在预热的插件
            if plugin_id in self.warming_up_plugins:
                continue

            # 转换为对象
            metrics = PluginMetrics.from_dict(plugin_id, metrics_dict)

            # 检查使用频率
            if metrics.total_invokes >= self.warmup_config.min_usage_count:
                # 计算使用频率评分
                frequency_score = self._calculate_frequency_score(
                    metrics, current_time, cutoff_time
                )

                if frequency_score > 0:
                    candidate = PluginCandidate(
                        plugin_id=plugin_id,
                        frequency_score=frequency_score,
                        total_invokes=metrics.total_invokes,
                        avg_startup_time_ms=metrics.avg_startup_time_ms,
                        last_accessed=metrics.last_accessed,
                        success_rate=metrics.success_rate_percent,
                    )
                    candidates.append(candidate)

        # 按频率评分排序
        candidates.sort(key=lambda x: x.frequency_score, reverse=True)

        # 限制预热插件数量
        max_plugins = self.warmup_config.max_warmup_plugins
        return candidates[:max_plugins]

    def _calculate_frequency_score(
        self,
        metrics: PluginMetrics,
        current_time: datetime,
        cutoff_time: datetime,
    ) -> float:
        """计算插件使用频率评分"""
        total_invokes = metrics.total_invokes
        last_accessed = metrics.last_accessed
        success_rate = metrics.success_rate_percent
        avg_startup_time = metrics.avg_startup_time_ms

        # 基础频率评分
        frequency_score = float(total_invokes)

        # 时间衰减因子（最近访问的权重更高）
        if last_accessed:
            if isinstance(last_accessed, datetime):
                days_since_access = (current_time - last_accessed).days
                time_factor = max(0.1, 1.0 - (days_since_access / 30))  # 30天完全衰减
                frequency_score *= time_factor

        # 成功率加成
        if success_rate > 80:
            frequency_score *= 1.2
        elif success_rate < 50:
            frequency_score *= 0.5

        # 启动时间惩罚（启动越慢，预热价值越高）
        if avg_startup_time > 1000:  # 超过1秒启动时间
            frequency_score *= 1.5

        return frequency_score

    async def warmup_plugin(self, session: AsyncSession, plugin_id: str) -> SinglePluginWarmupResult:
        """预热单个插件"""
        if plugin_id in self.warming_up_plugins:
            self.logger.warning(f"插件正在预热中: {plugin_id}")
            return SinglePluginWarmupResult(
                plugin_id=plugin_id,
                result=PluginWarmupResult.ALREADY_WARMING,
                error_message="插件正在预热中",
            )

        if plugin_id in self.plugin_manager.running_plugins:
            self.logger.debug(f"插件已在运行，无需预热: {plugin_id}")
            self.warmed_plugins.add(plugin_id)
            return SinglePluginWarmupResult(
                plugin_id=plugin_id, result=PluginWarmupResult.ALREADY_RUNNING
            )

        self.logger.info(f"开始预热插件: {plugin_id}")
        self.warming_up_plugins.add(plugin_id)

        try:
            warmup_start_time = time.time()

            # 确保插件准备就绪（下载+启动）
            success = await self.plugin_manager._ensure_plugin_ready(session, plugin_id)

            warmup_time = time.time() - warmup_start_time

            if success:
                self.warmed_plugins.add(plugin_id)
                self.logger.info(
                    f"插件预热成功: {plugin_id} (用时: {warmup_time:.3f}秒)"
                )

                # 记录预热时间作为启动时间
                self.performance_monitor.record_startup_time(plugin_id, warmup_time)

                return SinglePluginWarmupResult(
                    plugin_id=plugin_id,
                    result=PluginWarmupResult.SUCCESS,
                    warmup_time_seconds=warmup_time,
                )
            else:
                self.logger.warning(f"插件预热失败: {plugin_id}")
                return SinglePluginWarmupResult(
                    plugin_id=plugin_id,
                    result=PluginWarmupResult.FAILED,
                    warmup_time_seconds=warmup_time,
                    error_message="插件启动失败",
                )

        except Exception as e:
            self.logger.exception(f"插件预热异常: {plugin_id}")
            return SinglePluginWarmupResult(
                plugin_id=plugin_id,
                result=PluginWarmupResult.FAILED,
                error_message=str(e),
            )

        finally:
            self.warming_up_plugins.discard(plugin_id)

    async def auto_warmup(self, session: AsyncSession) -> WarmupExecutionResult:
        """自动预热插件"""
        if not self.warmup_config.enabled:
            return WarmupExecutionResult(status=WarmupStatus.DISABLED)

        execution_start_time = time.time()
        self.logger.info("开始自动预热分析...")

        # 分析预热候选插件
        candidates = await self.analyze_warmup_candidates()

        if not candidates:
            self.logger.info("没有找到合适的预热候选插件")
            return WarmupExecutionResult(
                status=WarmupStatus.NO_CANDIDATES,
                execution_time_seconds=time.time() - execution_start_time,
            )

        warmed_plugins = []
        failed_plugins = []

        self.logger.info(f"发现 {len(candidates)} 个预热候选插件")

        # 并发预热（限制并发数）
        semaphore = asyncio.Semaphore(3)  # 最多同时预热3个插件

        async def warmup_with_semaphore(candidate: PluginCandidate):
            async with semaphore:
                plugin_id = candidate.plugin_id
                self.logger.info(
                    f"预热插件: {plugin_id} (评分: {candidate.frequency_score:.2f})"
                )

                result = await self.warmup_plugin(session, plugin_id)
                if result.result == PluginWarmupResult.SUCCESS:
                    warmed_plugins.append(candidate)
                else:
                    failed_plugins.append(candidate)

        # 执行并发预热
        await asyncio.gather(
            *[warmup_with_semaphore(candidate) for candidate in candidates],
            return_exceptions=True,
        )

        self.last_warmup_time = datetime.now()
        execution_time = time.time() - execution_start_time

        result = WarmupExecutionResult(
            status=WarmupStatus.COMPLETED,
            warmed_plugins=warmed_plugins,
            failed_plugins=failed_plugins,
            warmup_time=self.last_warmup_time,
            total_candidates=len(candidates),
            execution_time_seconds=execution_time,
        )

        self.logger.info(
            f"自动预热完成: {len(warmed_plugins)} 成功, {len(failed_plugins)} 失败"
        )
        return result

    async def startup_warmup(self, session: AsyncSession) -> WarmupExecutionResult:
        """启动时预热"""
        if not self.warmup_config.warmup_on_startup:
            return WarmupExecutionResult(status=WarmupStatus.DISABLED)

        self.logger.info("执行启动时预热...")
        return await self.auto_warmup(session)

    async def get_warmup_status(self) -> WarmupStatusInfo:
        """获取预热状态"""
        return WarmupStatusInfo(
            enabled=self.warmup_config.enabled,
            warming_up_plugins=list(self.warming_up_plugins),
            warmed_plugins=list(self.warmed_plugins),
            warmup_config=self.warmup_config,
            last_warmup_time=self.last_warmup_time,
        )

    async def configure_warmup(self, config: WarmupConfig) -> bool:
        """配置预热参数"""
        try:
            # 更新配置
            self.warmup_config = config
            self.logger.info(f"更新预热配置: {config}")
            return True
        except Exception as e:
            self.logger.exception("配置预热参数失败")
            return False

    async def update_warmup_config(self, **kwargs) -> bool:
        """更新预热配置的部分参数"""
        try:
            # 创建新的配置对象，保留原有值但更新传入的值
            config_dict = self.warmup_config.model_dump()
            config_dict.update(kwargs)

            # 验证配置
            new_config = WarmupConfig(**config_dict)
            self.warmup_config = new_config

            self.logger.info(f"部分更新预热配置: {kwargs}")
            return True
        except Exception as e:
            self.logger.exception("更新预热配置失败")
            return False
