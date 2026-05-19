"""
RedisUtil 工具类测试

测试覆盖场景：
- 字符串操作（set/get/delete）
- 获取不存在的键
- 健康检查
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRedisUtilInit:
    """RedisUtil 初始化测试"""

    @pytest.mark.asyncio
    async def test_init_with_single_mode(self):
        """
        场景：单机模式连接
        WHEN: 配置 redis.mode=single
        THEN: 系统创建单机 Redis 连接池
        """
        from framework.cache.redis_util import RedisUtil
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.mode = "single"
        mock_config.single.host = "localhost"
        mock_config.single.port = 6379
        mock_config.single.db = 0
        # 不设置 connection_pool，使用默认值
        mock_config.single.connection_pool = None

        await RedisUtil.init(mock_config)

        assert RedisUtil._client is not None
        assert RedisUtil._pool is not None

        # 清理
        await RedisUtil.close()


class TestRedisUtilStringOperations:
    """RedisUtil 字符串操作测试"""

    @pytest.fixture
    def mock_redis(self):
        """创建模拟 Redis 客户端"""
        client = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, mock_redis):
        """
        场景：字符串操作
        WHEN: 调用 RedisUtil.set("key", "value", ttl=60)
        THEN: Redis 存储键值对，60 秒后过期
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.set.return_value = True

            result = await RedisUtil.set("key", "value", ttl=60)

            assert result is True
            mock_redis.set.assert_called_once_with("key", "value", ex=60, nx=False)

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, mock_redis):
        """
        场景：字符串操作（无过期时间）
        WHEN: 调用 RedisUtil.set("key", "value")
        THEN: Redis 存储键值对，无过期时间
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.set.return_value = True

            result = await RedisUtil.set("key", "value")

            assert result is True
            mock_redis.set.assert_called_once_with("key", "value", ex=None, nx=False)

    @pytest.mark.asyncio
    async def test_get_existing_key(self, mock_redis):
        """
        场景：获取存在的键
        WHEN: 调用 RedisUtil.get("key")
        THEN: 返回对应的值
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.get.return_value = b"value"

            result = await RedisUtil.get("key")

            assert result == "value"
            mock_redis.get.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, mock_redis):
        """
        场景：获取不存在的键
        WHEN: 调用 RedisUtil.get("nonexistent")
        THEN: 返回 None
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.get.return_value = None

            result = await RedisUtil.get("nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, mock_redis):
        """
        场景：删除键
        WHEN: 调用 RedisUtil.delete("key")
        THEN: 键被删除，返回删除数量
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.delete.return_value = 1

            result = await RedisUtil.delete("key")

            assert result == 1
            mock_redis.delete.assert_called_once_with("key")


class TestRedisUtilHealthCheck:
    """RedisUtil 健康检查测试"""

    @pytest.fixture
    def mock_redis(self):
        """创建模拟 Redis 客户端"""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_redis):
        """
        场景：健康检查成功
        WHEN: 调用 RedisUtil.health_check()
        THEN: 返回 True（连接正常）
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.ping.return_value = True

            result = await RedisUtil.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_redis):
        """
        场景：健康检查失败
        WHEN: Redis 服务不可用时调用 RedisUtil.health_check()
        THEN: 返回 False
        """
        from framework.cache.redis_util import RedisUtil

        with patch.object(RedisUtil, '_client', mock_redis):
            mock_redis.ping.side_effect = ConnectionError("Redis unavailable")

            result = await RedisUtil.health_check()

            assert result is False


class TestRedisUtilConnectionPool:
    """连接池管理测试"""

    @pytest.mark.asyncio
    async def test_connection_pool_config(self):
        """
        场景：连接池配置
        WHEN: 配置 redis.single.connection-pool.max-connections=50
        THEN: 连接池最大连接数为 50
        """
        from framework.cache.redis_util import RedisUtil
        from unittest.mock import MagicMock, patch, AsyncMock

        mock_config = MagicMock()
        mock_config.mode = "single"
        mock_config.single.host = "localhost"
        mock_config.single.port = 6379
        mock_config.single.db = 0
        mock_config.single.connection_pool.max_connections = 50

        with patch('framework.cache.redis_util.ConnectionPool') as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool.disconnect = AsyncMock()
            mock_pool_class.return_value = mock_pool

            with patch('framework.cache.redis_util.Redis') as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis.close = AsyncMock()
                mock_redis_class.return_value = mock_redis

                await RedisUtil.init(mock_config)

                # 验证连接池参数
                call_kwargs = mock_pool_class.call_args[1]
                assert call_kwargs['max_connections'] == 50

        await RedisUtil.close()
