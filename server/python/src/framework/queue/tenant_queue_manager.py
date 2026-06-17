"""
租户队列管理器

提供租户级队列资源管理，支持：
- 独立队列实例物理隔离
- 默认队列实例 + Key 前缀逻辑隔离
- 队列客户端缓存（委托给 TenantCacheManager）
"""

from typing import Any

from loguru import logger

from framework.tenant.context import get_tenant_id
from framework.tenant.protocols import TenantQueueConfig
from framework.database.mixins.tenant import should_skip_tenant

_logger = logger.bind(name=__name__)

# 队列名格式
TENANT_QUEUE_PREFIX = "{tenant_id}:queue:{queue_name}"


class TenantQueueManager:
    """
    租户队列管理器

    委托给 TenantCacheManager 进行 Redis Stream 操作。
    支持队列名隔离（物理隔离 vs 逻辑隔离）。
    """

    def __init__(self, cache_manager):
        """
        初始化队列管理器

        Args:
            cache_manager: TenantCacheManager 实例
        """
        self._cache_manager = cache_manager

    @staticmethod
    def _is_physical_isolation(config: TenantQueueConfig | None) -> bool:
        """判断是否使用物理隔离"""
        return bool(config and config.host)

    def _build_queue_name(
        self,
        queue_name: str,
        tenant_id: str | None = None,
        config: TenantQueueConfig | None = None,
        skip_tenant: bool = False,
    ) -> str:
        """
        构建队列名

        Args:
            queue_name: 原始队列名
            tenant_id: 租户 ID
            config: 队列配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 实际队列名
        """
        if skip_tenant or should_skip_tenant():
            return f"queue:{queue_name}"

        # 物理隔离或独立队列，不添加前缀
        if self._is_physical_isolation(config):
            return f"queue:{queue_name}"

        # 使用默认实例，添加租户前缀
        actual_tenant_id = tenant_id or get_tenant_id()
        if actual_tenant_id:
            return TENANT_QUEUE_PREFIX.format(
                tenant_id=actual_tenant_id,
                queue_name=queue_name,
            )

        return f"queue:{queue_name}"

    async def xadd(
        self,
        queue_name: str,
        fields: dict[str, Any],
        tenant_id: str | None = None,
        config: TenantQueueConfig | None = None,
        id: str = "*",
        skip_tenant: bool = False,
    ) -> str:
        """
        发送消息到队列

        Args:
            queue_name: 队列名
            fields: 消息字段
            tenant_id: 租户 ID
            config: 队列配置
            id: 消息 ID
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 消息 ID
        """
        actual_stream = self._build_queue_name(queue_name, tenant_id, config, skip_tenant)

        from framework.tenant.protocols import TenantCacheConfig

        cache_config = None
        if self._is_physical_isolation(config):
            assert config is not None
            cache_config = TenantCacheConfig(
                host=config.host,
                port=config.port,
                password=config.password,
            )

        return await self._cache_manager.xadd(
            queue_name=actual_stream.replace("queue:", ""),
            fields=fields,
            tenant_id=tenant_id,
            config=cache_config,
            id=id,
            skip_tenant=True,  # queue name already built
        )

    async def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        queue_name: str,
        tenant_id: str | None = None,
        config: TenantQueueConfig | None = None,
        count: int = 1,
        block: int | None = None,
        skip_tenant: bool = False,
    ) -> list:
        """
        消费队列消息

        Args:
            groupname: 消费者组名
            consumername: 消费者名
            queue_name: 队列名
            tenant_id: 租户 ID
            config: 队列配置
            count: 消息数量
            block: 阻塞时间（毫秒）
            skip_tenant: 是否跳过租户前缀

        Returns:
            list: 消息列表
        """
        actual_stream = self._build_queue_name(queue_name, tenant_id, config, skip_tenant)

        from framework.tenant.protocols import TenantCacheConfig

        cache_config = None
        if self._is_physical_isolation(config):
            assert config is not None
            cache_config = TenantCacheConfig(
                host=config.host,
                port=config.port,
                password=config.password,
            )

        return await self._cache_manager.xreadgroup(
            groupname=groupname,
            consumername=consumername,
            queue_name=actual_stream.replace("queue:", ""),
            tenant_id=tenant_id,
            config=cache_config,
            count=count,
            block=block,
            skip_tenant=True,
        )

    async def xack(
        self,
        queue_name: str,
        group: str,
        *ids: str,
        tenant_id: str | None = None,
        config: TenantQueueConfig | None = None,
        skip_tenant: bool = False,
    ) -> int:
        """
        确认消息

        Args:
            queue_name: 队列名
            group: 消费者组
            ids: 消息 ID 列表
            tenant_id: 租户 ID
            config: 队列配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            int: 确认的消息数
        """
        actual_stream = self._build_queue_name(queue_name, tenant_id, config, skip_tenant)

        from framework.tenant.protocols import TenantCacheConfig

        cache_config = None
        if self._is_physical_isolation(config):
            assert config is not None
            cache_config = TenantCacheConfig(
                host=config.host,
                port=config.port,
                password=config.password,
            )

        return await self._cache_manager.xack(
            actual_stream.replace("queue:", ""),
            group,
            *ids,
            tenant_id=tenant_id,
            config=cache_config,
            skip_tenant=True,
        )


# 全局队列管理器实例
_queue_manager: TenantQueueManager | None = None


def get_queue_manager() -> TenantQueueManager:
    """
    获取全局队列管理器实例

    Returns:
        TenantQueueManager: 队列管理器实例
    """
    global _queue_manager
    if _queue_manager is None:
        raise RuntimeError("TenantQueueManager 未初始化")
    return _queue_manager


def init_queue_manager(cache_manager) -> TenantQueueManager:
    """
    初始化队列管理器

    Args:
        cache_manager: TenantCacheManager 实例

    Returns:
        TenantQueueManager: 队列管理器实例
    """
    global _queue_manager
    _queue_manager = TenantQueueManager(cache_manager)
    return _queue_manager
