"""
租户发布订阅管理器

提供租户级发布订阅资源管理，支持：
- 独立消息实例物理隔离
- 默认消息实例 + 频道前缀逻辑隔离
- 频道名隔离
"""

from loguru import logger

from framework.tenant.context import get_tenant_id
from framework.tenant.protocols import TenantPubSubConfig
from framework.database.mixins.tenant import should_skip_tenant

_logger = logger.bind(name=__name__)

# 频道名格式
TENANT_CHANNEL_PREFIX = "{tenant_id}:channel:{channel_name}"


class TenantPubSubManager:
    """
    租户发布订阅管理器

    委托给 TenantCacheManager 进行 Redis PubSub 操作。
    支持频道名隔离（物理隔离 vs 逻辑隔离）。
    """

    def __init__(self, cache_manager):
        """
        初始化发布订阅管理器

        Args:
            cache_manager: TenantCacheManager 实例
        """
        self._cache_manager = cache_manager

    @staticmethod
    def _is_physical_isolation(config: TenantPubSubConfig | None) -> bool:
        """判断是否使用物理隔离"""
        return bool(config and config.host)

    def _build_channel_name(
        self,
        channel: str,
        tenant_id: str | None = None,
        config: TenantPubSubConfig | None = None,
        skip_tenant: bool = False,
    ) -> str:
        """
        构建频道名

        Args:
            channel: 原始频道名
            tenant_id: 租户 ID
            config: 发布订阅配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            str: 实际频道名
        """
        if skip_tenant or should_skip_tenant():
            return channel

        # 物理隔离，不添加前缀
        if self._is_physical_isolation(config):
            return channel

        # 使用默认实例，添加租户前缀
        actual_tenant_id = tenant_id or get_tenant_id()
        if actual_tenant_id:
            return TENANT_CHANNEL_PREFIX.format(
                tenant_id=actual_tenant_id,
                channel_name=channel,
            )

        return channel

    async def publish(
        self,
        channel: str,
        message: str,
        tenant_id: str | None = None,
        config: TenantPubSubConfig | None = None,
        skip_tenant: bool = False,
    ) -> int:
        """
        发布消息到频道

        Args:
            channel: 频道名
            message: 消息内容
            tenant_id: 租户 ID
            config: 发布订阅配置
            skip_tenant: 是否跳过租户前缀

        Returns:
            int: 订阅者数量
        """
        actual_channel = self._build_channel_name(channel, tenant_id, config, skip_tenant)

        from framework.tenant.protocols import TenantCacheConfig

        cache_config = None
        if self._is_physical_isolation(config):
            assert config is not None
            cache_config = TenantCacheConfig(
                host=config.host,
                port=config.port,
                password=config.password,
            )

        return await self._cache_manager.publish(
            channel=actual_channel,
            message=message,
            tenant_id=tenant_id,
            config=cache_config,
            skip_tenant=True,  # channel name already built
        )

    async def subscribe(
        self,
        channel: str,
        tenant_id: str | None = None,
        config: TenantPubSubConfig | None = None,
    ):
        """
        订阅频道

        Args:
            channel: 频道名
            tenant_id: 租户 ID
            config: 发布订阅配置

        Returns:
            订阅对象
        """
        actual_channel = self._build_channel_name(channel, tenant_id, config)

        from framework.tenant.protocols import TenantCacheConfig

        cache_config = None
        if self._is_physical_isolation(config):
            assert config is not None
            cache_config = TenantCacheConfig(
                host=config.host,
                port=config.port,
                password=config.password,
            )

        client = await self._cache_manager.get_client(tenant_id, cache_config)
        pubsub = client.pubsub()
        await pubsub.subscribe(actual_channel)
        _logger.debug(f"订阅频道: {actual_channel}")
        return pubsub

    async def unsubscribe(self, pubsub, channel: str) -> None:
        """
        取消订阅

        Args:
            pubsub: 订阅对象
            channel: 频道名
        """
        await pubsub.unsubscribe(channel)


# 全局发布订阅管理器实例
_pubsub_manager: TenantPubSubManager | None = None


def get_pubsub_manager() -> TenantPubSubManager:
    """
    获取全局发布订阅管理器实例

    Returns:
        TenantPubSubManager: 发布订阅管理器实例
    """
    global _pubsub_manager
    if _pubsub_manager is None:
        raise RuntimeError("TenantPubSubManager 未初始化")
    return _pubsub_manager


def init_pubsub_manager(cache_manager) -> TenantPubSubManager:
    """
    初始化发布订阅管理器

    Args:
        cache_manager: TenantCacheManager 实例

    Returns:
        TenantPubSubManager: 发布订阅管理器实例
    """
    global _pubsub_manager
    _pubsub_manager = TenantPubSubManager(cache_manager)
    return _pubsub_manager
