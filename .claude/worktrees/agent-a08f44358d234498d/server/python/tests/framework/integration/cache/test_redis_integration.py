"""
Redis 缓存集成测试

测试 RedisUtil 与真实 Redis 服务的交互。
使用 @pytest.mark.integration 标记。
"""

import asyncio

import pytest
import pytest_asyncio

from framework.cache.redis_util import RedisUtil
from framework.core.lock import Lock


pytestmark = pytest.mark.integration


class TestRedisStringOperations:
    """Redis 字符串操作集成测试"""

    @pytest_asyncio.fixture
    async def cleanup_key(self, redis_client, redis_key_prefix):
        """测试后清理键"""
        key = f"{redis_key_prefix}string_test"
        yield key
        await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, redis_client, redis_key_prefix, cleanup_key):
        """
        场景：字符串操作
        WHEN: 调用 RedisUtil.set 设置键值对并指定 TTL
        THEN: 键值正确存储，过期时间正确设置
        """
        key = cleanup_key
        value = "test_value"

        # 设置带 TTL 的键值对
        result = await redis_client.set(key, value, ttl=60)
        assert result is True

        # 验证键值
        stored = await redis_client.get(key)
        assert stored == value

        # 验证 TTL 设置（应该大于 0）
        ttl = await redis_client._client.ttl(key)
        assert ttl > 0
        assert ttl <= 60

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, redis_client, redis_key_prefix):
        """
        场景：字符串操作（无过期时间）
        WHEN: 调用 RedisUtil.set 不指定 TTL
        THEN: 键值正确存储，无过期时间
        """
        key = f"{redis_key_prefix}no_ttl"
        value = "persistent_value"

        try:
            result = await redis_client.set(key, value)
            assert result is True

            stored = await redis_client.get(key)
            assert stored == value

            # TTL 应该是 -1（永不过期）
            ttl = await redis_client._client.ttl(key)
            assert ttl == -1
        finally:
            await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_get_existing_key(self, redis_client, redis_key_prefix):
        """
        场景：键值获取
        WHEN: 调用 RedisUtil.get 获取存在的键
        THEN: 返回正确的值
        """
        key = f"{redis_key_prefix}get_test"
        value = "retrieve_value"

        try:
            await redis_client.set(key, value)
            result = await redis_client.get(key)
            assert result == value
        finally:
            await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis_client):
        """
        场景：获取不存在的键
        WHEN: 调用 RedisUtil.get 获取不存在的键
        THEN: 返回 None
        """
        result = await redis_client.get("nonexistent_key_12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, redis_client, redis_key_prefix):
        """
        场景：键值删除
        WHEN: 调用 RedisUtil.delete 删除键
        THEN: 键被成功删除
        """
        key = f"{redis_key_prefix}delete_test"
        value = "to_be_deleted"

        # 设置键
        await redis_client.set(key, value)

        # 验证键存在
        assert await redis_client.exists(key)

        # 删除键
        result = await redis_client.delete(key)
        assert result == 1

        # 验证键不存在
        assert not await redis_client.exists(key)

    @pytest.mark.asyncio
    async def test_set_nx_option(self, redis_client, redis_key_prefix):
        """
        场景：NX 选项测试
        WHEN: 使用 nx=True 设置键
        THEN: 仅当键不存在时设置成功
        """
        key = f"{redis_key_prefix}nx_test"
        value1 = "first_value"
        value2 = "second_value"

        try:
            # 第一次设置应该成功
            result1 = await redis_client.set(key, value1, nx=True)
            assert result1 is True

            # 第二次设置应该失败（键已存在）
            result2 = await redis_client.set(key, value2, nx=True)
            assert result2 is None or result2 is False

            # 值应该是第一次设置的
            stored = await redis_client.get(key)
            assert stored == value1
        finally:
            await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_incr_decr(self, redis_client, redis_key_prefix):
        """
        场景：数值操作
        WHEN: 使用 incr/decr 操作
        THEN: 正确递增/递减
        """
        key = f"{redis_key_prefix}counter"

        try:
            # 初始递增
            result = await redis_client.incr(key)
            assert result == 1

            # 再次递增
            result = await redis_client.incr(key, 5)
            assert result == 6

            # 递减
            result = await redis_client.decr(key, 2)
            assert result == 4
        finally:
            await redis_client.delete(key)


class TestRedisHashOperations:
    """Redis Hash 操作集成测试"""

    @pytest.mark.asyncio
    async def test_hash_operations(self, redis_client, redis_key_prefix):
        """
        场景：Hash 操作
        WHEN: 使用 hset/hget/hdel 操作
        THEN: 正确存储和获取
        """
        key = f"{redis_key_prefix}hash"

        try:
            # 设置 Hash 字段
            await redis_client.hset(key, "field1", "value1")
            await redis_client.hset(key, "field2", "value2")

            # 获取字段
            result = await redis_client.hget(key, "field1")
            assert result == "value1"

            # 获取所有字段
            all_fields = await redis_client.hgetall(key)
            assert all_fields == {"field1": "value1", "field2": "value2"}

            # 删除字段
            await redis_client.hdel(key, "field1")
            assert not await redis_client.hexists(key, "field1")
        finally:
            await redis_client.delete(key)


class TestRedisListOperations:
    """Redis List 操作集成测试"""

    @pytest.mark.asyncio
    async def test_list_operations(self, redis_client, redis_key_prefix):
        """
        场景：List 操作
        WHEN: 使用 lpush/rpush/lpop/rpop 操作
        THEN: 正确入队出队
        """
        key = f"{redis_key_prefix}list"

        try:
            # 从左侧推入
            await redis_client.lpush(key, "first")
            await redis_client.lpush(key, "second")

            # 检查长度
            length = await redis_client.llen(key)
            assert length == 2

            # 从右侧弹出
            result = await redis_client.rpop(key)
            assert result == "first"

            # 从左侧弹出
            result = await redis_client.lpop(key)
            assert result == "second"
        finally:
            await redis_client.delete(key)


class TestRedisSetOperations:
    """Redis Set 操作集成测试"""

    @pytest.mark.asyncio
    async def test_set_operations(self, redis_client, redis_key_prefix):
        """
        场景：Set 操作
        WHEN: 使用 sadd/srem/sismember 操作
        THEN: 正确添加和移除成员
        """
        key = f"{redis_key_prefix}set"

        try:
            # 添加成员
            await redis_client.sadd(key, "member1", "member2", "member3")

            # 检查成员存在
            assert await redis_client.sismember(key, "member1")
            assert await redis_client.sismember(key, "member2")

            # 获取所有成员
            members = await redis_client.smembers(key)
            assert members == {"member1", "member2", "member3"}

            # 移除成员
            await redis_client.srem(key, "member1")
            assert not await redis_client.sismember(key, "member1")
        finally:
            await redis_client.delete(key)


class TestRedisHealthCheck:
    """Redis 健康检查集成测试"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_client):
        """
        场景：健康检查
        WHEN: 调用 RedisUtil.health_check
        THEN: 服务可用时返回 True
        """
        result = await redis_client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_operation(self, redis_client, redis_key_prefix):
        """
        场景：键存在检查
        WHEN: 调用 exists 检查键
        THEN: 正确返回存在状态
        """
        key = f"{redis_key_prefix}exists_test"

        try:
            # 键不存在
            assert not await redis_client.exists(key)

            # 设置键后存在
            await redis_client.set(key, "value")
            assert await redis_client.exists(key)
        finally:
            await redis_client.delete(key)


class TestRedisConnectionPool:
    """Redis 连接池集成测试"""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, redis_client, redis_key_prefix):
        """
        场景：并发操作
        WHEN: 多个并发请求
        THEN: 连接池正确处理
        """
        async def set_get_delete(i: int):
            key = f"{redis_key_prefix}concurrent_{i}"
            value = f"value_{i}"
            await redis_client.set(key, value)
            result = await redis_client.get(key)
            await redis_client.delete(key)
            return result == value

        # 并发执行 10 个操作
        results = await asyncio.gather(*[set_get_delete(i) for i in range(10)])

        assert all(results)

    @pytest.mark.asyncio
    async def test_expire_operation(self, redis_client, redis_key_prefix):
        """
        场景：过期时间设置
        WHEN: 使用 expire 设置过期时间
        THEN: 键在指定时间后过期
        """
        key = f"{redis_key_prefix}expire_test"

        try:
            await redis_client.set(key, "value")

            # 设置过期时间
            result = await redis_client.expire(key, 1)
            assert result is True

            # 等待过期
            await asyncio.sleep(1.5)

            # 键应该已过期
            result = await redis_client.get(key)
            assert result is None
        finally:
            await redis_client.delete(key)
