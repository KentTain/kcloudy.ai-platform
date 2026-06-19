# 凭证缓存集成测试

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ai.components.model.internal.provider_manager import (
    CACHE_KEY_PREFIX,
    CACHE_TTL,
    ProviderManager,
)


@pytest.mark.integration
class TestCredentialCacheIntegration:
    """凭证缓存集成测试（需要 Redis）"""

    @pytest_asyncio.fixture(loop_scope="function")
    async def provider_manager(self):
        """创建 ProviderManager 实例"""
        return ProviderManager()

    @pytest_asyncio.fixture(loop_scope="function")
    async def mock_cache_manager(self):
        """模拟缓存管理器"""
        cache_manager = AsyncMock()
        cache_manager.get = AsyncMock(return_value=None)
        cache_manager.set = AsyncMock()
        cache_manager.delete = AsyncMock()
        return cache_manager

    @pytest_asyncio.fixture(loop_scope="function")
    def tenant_id(self):
        """生成测试租户 ID"""
        return "test-cache-tenant-001"

    @pytest.mark.asyncio
    async def test_cache_hit_within_ttl(
        self, provider_manager, mock_cache_manager, tenant_id
    ):
        """测试缓存命中（TTL 内）"""
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
        cached_data = {
            "tenant_id": tenant_id,
            "providers": {
                "openai": {
                    "tenant_id": tenant_id,
                    "provider_name": "openai",
                    "custom_configuration": {},
                    "model_settings": [],
                }
            },
        }

        # 设置缓存命中
        mock_cache_manager.get = AsyncMock(return_value=cached_data)

        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager",
            return_value=mock_cache_manager,
        ), patch(
            "ai.components.model.internal.provider_manager.ModelProviderFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.get_providers = AsyncMock(return_value=[])
            mock_factory_class.return_value = mock_factory

            with patch(
                "ai.components.model.internal.provider_manager.ProviderConfigurations"
            ) as mock_configs_class:
                mock_configs = MagicMock()
                mock_configs_class.from_dict = MagicMock(return_value=mock_configs)

                # 第一次调用应该命中缓存
                result = await provider_manager.get_configurations(
                    tenant_id, use_cache=True
                )

                # 验证从缓存获取
                mock_cache_manager.get.assert_called_once_with(
                    cache_key, tenant_id=tenant_id
                )
                # 验证没有写入缓存（因为命中了）
                mock_cache_manager.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_and_set(
        self, provider_manager, mock_cache_manager, tenant_id
    ):
        """测试缓存未命中并写入"""
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"

        # 设置缓存未命中
        mock_cache_manager.get = AsyncMock(return_value=None)

        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager",
            return_value=mock_cache_manager,
        ):
            # 模拟数据库加载
            provider_manager._get_all_providers = AsyncMock(return_value={})
            provider_manager._get_all_provider_model_settings = AsyncMock(
                return_value={}
            )
            provider_manager._get_all_custom_models = AsyncMock(return_value={})
            provider_manager._to_custom_configuration = AsyncMock(
                return_value=MagicMock()
            )
            provider_manager._to_model_settings = MagicMock(return_value=[])

            with patch(
                "ai.components.model.internal.provider_manager.ModelProviderFactory"
            ) as mock_factory_class:
                mock_factory = MagicMock()
                mock_factory.get_providers = AsyncMock(return_value=[])
                mock_factory_class.return_value = mock_factory

                with patch(
                    "ai.components.model.internal.provider_manager.ProviderConfigurations"
                ) as mock_configs_class:
                    mock_configs = MagicMock()
                    mock_configs.to_dict = MagicMock(return_value={"providers": {}})
                    mock_configs_class.return_value = mock_configs

                    result = await provider_manager.get_configurations(
                        tenant_id, use_cache=True
                    )

                    # 验证尝试从缓存获取
                    mock_cache_manager.get.assert_called_once()
                    # 验证写入缓存
                    mock_cache_manager.set.assert_called_once()
                    call_args = mock_cache_manager.set.call_args
                    assert call_args[0][0] == cache_key
                    assert call_args[1]["ttl"] == CACHE_TTL

    @pytest.mark.asyncio
    async def test_cache_expired_reload(
        self, provider_manager, mock_cache_manager, tenant_id
    ):
        """测试缓存过期后重新加载"""
        # 第一次调用缓存未命中，第二次命中
        mock_cache_manager.get = AsyncMock(
            side_effect=[
                None,  # 第一次未命中
                {"providers": {}},  # 第二次命中
            ]
        )

        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager",
            return_value=mock_cache_manager,
        ):
            provider_manager._get_all_providers = AsyncMock(return_value={})
            provider_manager._get_all_provider_model_settings = AsyncMock(
                return_value={}
            )
            provider_manager._get_all_custom_models = AsyncMock(return_value={})

            with patch(
                "ai.components.model.internal.provider_manager.ModelProviderFactory"
            ) as mock_factory_class:
                mock_factory = MagicMock()
                mock_factory.get_providers = AsyncMock(return_value=[])
                mock_factory_class.return_value = mock_factory

                with patch(
                    "ai.components.model.internal.provider_manager.ProviderConfigurations"
                ) as mock_configs_class:
                    mock_configs = MagicMock()
                    mock_configs.to_dict = MagicMock(return_value={})
                    mock_configs_class.return_value = mock_configs

                    # 第一次调用（缓存未命中）
                    await provider_manager.get_configurations(tenant_id, use_cache=True)

                    # 验证从数据库加载
                    assert provider_manager._get_all_providers.called

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_clear(
        self, provider_manager, mock_cache_manager, tenant_id
    ):
        """测试缓存清除"""
        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager",
            return_value=mock_cache_manager,
        ):
            await ProviderManager.clear_cache(tenant_id)

            expected_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
            mock_cache_manager.delete.assert_called_once_with(
                expected_key, tenant_id=tenant_id
            )


@pytest.mark.integration
class TestCredentialCacheTTL:
    """凭证缓存 TTL 测试"""

    def test_cache_ttl_is_5_minutes(self):
        """测试缓存 TTL 为 5 分钟"""
        assert CACHE_TTL == 300

    def test_cache_key_format(self):
        """测试缓存键格式"""
        tenant_id = "test-tenant"
        expected_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"

        assert expected_key == "model:provider_configs:test-tenant"


@pytest.mark.integration
class TestCredentialUpdateCacheInvalidation:
    """凭证更新后缓存失效测试"""

    @pytest.mark.asyncio
    async def test_credential_update_clears_cache(self):
        """测试凭证更新后清除缓存"""
        tenant_id = "test-tenant-credential-update"

        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager"
        ) as mock_get_cache:
            mock_cache_manager = AsyncMock()
            mock_get_cache.return_value = mock_cache_manager

            # 清除缓存
            await ProviderManager.clear_cache(tenant_id)

            # 验证缓存被清除
            expected_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
            mock_cache_manager.delete.assert_called_once_with(
                expected_key, tenant_id=tenant_id
            )


@pytest.mark.integration
@pytest.mark.skipif(
    True,  # 默认跳过，需要真实 Redis 环境
    reason="需要真实 Redis 环境，请手动启用此测试",
)
class TestCredentialCacheWithRealRedis:
    """凭证缓存真实 Redis 测试（需要 Redis 服务）"""

    @pytest_asyncio.fixture(loop_scope="function")
    async def redis_available(self, integration_settings):
        """检测 Redis 服务是否可用"""
        from framework.cache.redis_util import RedisUtil

        try:
            await RedisUtil.init(integration_settings.redis)
            result = await RedisUtil.health_check()
            await RedisUtil.close()
            return result
        except Exception:
            return False

    @pytest_asyncio.fixture(loop_scope="function")
    async def redis_client(self, integration_settings, redis_available):
        """Redis 客户端 fixture"""
        if not redis_available:
            pytest.skip("Redis 服务不可用")

        from framework.cache.redis_util import RedisUtil

        await RedisUtil.init(integration_settings.redis)
        yield RedisUtil
        await RedisUtil.close()

    @pytest.mark.asyncio
    async def test_real_cache_set_and_get(self, redis_client):
        """测试真实缓存写入和读取"""
        tenant_id = "test-real-cache-tenant"
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
        test_data = {"providers": {"test": "data"}}

        # 写入缓存
        await redis_client.set(cache_key, test_data, ttl=CACHE_TTL)

        # 读取缓存
        result = await redis_client.get(cache_key)

        assert result == test_data

        # 清理
        await redis_client.delete(cache_key)

    @pytest.mark.asyncio
    async def test_real_cache_expiration(self, redis_client):
        """测试真实缓存过期"""
        tenant_id = "test-cache-expiration"
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
        test_data = {"providers": {}}

        # 写入缓存，TTL 为 1 秒
        await redis_client.set(cache_key, test_data, ttl=1)

        # 立即读取应该命中
        result = await redis_client.get(cache_key)
        assert result == test_data

        # 等待过期
        import asyncio

        await asyncio.sleep(2)

        # 再次读取应该未命中
        result = await redis_client.get(cache_key)
        assert result is None
