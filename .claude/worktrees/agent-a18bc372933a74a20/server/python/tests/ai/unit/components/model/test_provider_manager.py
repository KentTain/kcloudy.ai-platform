# ProviderManager 单元测试

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.components.model.internal.provider_manager import (
    ProviderManager,
    CACHE_KEY_PREFIX,
    CACHE_TTL,
)
from ai.components.model.errors.error import ProviderNotFoundError
from ai.models.model_config import ModelType


class TestProviderManagerInit:
    """ProviderManager 初始化测试"""

    def test_init(self):
        """测试初始化"""
        manager = ProviderManager()

        assert manager.decoding_rsa_key is None
        assert manager.decoding_cipher_rsa is None


class TestProviderManagerClearCache:
    """ProviderManager clear_cache 测试"""

    @pytest.mark.asyncio
    async def test_clear_cache_for_tenant(self):
        """测试清除指定租户缓存"""
        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager"
        ) as mock_get_cache:
            mock_cache_manager = AsyncMock()
            mock_get_cache.return_value = mock_cache_manager

            await ProviderManager.clear_cache(tenant_id="test-tenant")

            expected_key = f"{CACHE_KEY_PREFIX}:test-tenant"
            mock_cache_manager.delete.assert_called_once_with(
                expected_key, tenant_id="test-tenant"
            )

    @pytest.mark.asyncio
    async def test_clear_cache_all_tenants(self):
        """测试清除所有租户缓存"""
        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager"
        ) as mock_get_cache:
            mock_cache_manager = AsyncMock()
            mock_get_cache.return_value = mock_cache_manager

            # 当前实现只是记录日志，不执行删除
            await ProviderManager.clear_cache(tenant_id=None)

            # 不应该调用 delete
            mock_cache_manager.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_cache_error_handling(self):
        """测试清除缓存错误处理"""
        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager"
        ) as mock_get_cache:
            mock_cache_manager = AsyncMock()
            mock_cache_manager.delete.side_effect = Exception("缓存错误")
            mock_get_cache.return_value = mock_cache_manager

            # 不应抛出异常
            await ProviderManager.clear_cache(tenant_id="test-tenant")


class TestProviderManagerGetConfigurations:
    """ProviderManager get_configurations 测试"""

    @pytest.mark.asyncio
    async def test_get_configurations_from_cache(self):
        """测试从缓存获取配置"""
        manager = ProviderManager()
        tenant_id = "test-tenant"
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"

        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager"
        ) as mock_get_cache:
            mock_cache_manager = AsyncMock()
            mock_cache_manager.get = AsyncMock(
                return_value={
                    "tenant_id": tenant_id,
                    "providers": {},
                }
            )
            mock_get_cache.return_value = mock_cache_manager

            # 需要模拟 ModelProviderFactory
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
                    mock_configs.from_dict = MagicMock(return_value=mock_configs)
                    mock_configs_class.from_dict = MagicMock(return_value=mock_configs)

                    result = await manager.get_configurations(
                        tenant_id, use_cache=True
                    )

                    # 应该从缓存获取
                    mock_cache_manager.get.assert_called_once()


class TestProviderManagerGetProviderModelBundle:
    """ProviderManager _get_provider_model_bundle 测试"""

    @pytest.mark.asyncio
    async def test_get_provider_model_bundle_success(self):
        """测试获取供应商模型束"""
        manager = ProviderManager()
        tenant_id = "test-tenant"

        # 模拟配置
        mock_model_type_instance = MagicMock()
        mock_configuration = MagicMock()
        mock_configuration.provider = MagicMock()
        mock_configuration.provider.provider = "openai"
        mock_configuration.get_model_type_instance = AsyncMock(
            return_value=mock_model_type_instance
        )
        mock_configuration.get_current_credentials = MagicMock(return_value={"api_key": "test"})

        mock_configurations = MagicMock()
        mock_configurations.get = MagicMock(return_value=mock_configuration)

        manager.get_configurations = AsyncMock(return_value=mock_configurations)

        # 模拟 ModelProviderFactory
        with patch(
            "ai.components.model.internal.provider_manager.ModelProviderFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.get_providers = AsyncMock(return_value=[])
            mock_factory_class.return_value = mock_factory

            # 需要 ProviderModelBundle
            with patch(
                "ai.components.model.internal.provider_manager.ProviderModelBundle"
            ) as mock_bundle_class:
                mock_bundle = MagicMock()
                mock_bundle_class.return_value = mock_bundle

                result = await manager._get_provider_model_bundle(
                    tenant_id=tenant_id,
                    provider="openai",
                    model_type=ModelType.LLM,
                )

                assert result == mock_bundle

    @pytest.mark.asyncio
    async def test_get_provider_model_bundle_provider_not_found(self):
        """测试提供者不存在时抛出异常"""
        manager = ProviderManager()
        tenant_id = "test-tenant"

        # 模拟空配置
        mock_configurations = MagicMock()
        mock_configurations.get = MagicMock(return_value=None)

        manager.get_configurations = AsyncMock(return_value=mock_configurations)

        with pytest.raises(ProviderNotFoundError):
            await manager._get_provider_model_bundle(
                tenant_id=tenant_id,
                provider="nonexistent",
                model_type=ModelType.LLM,
            )


class TestCacheConstants:
    """缓存常量测试"""

    def test_cache_key_prefix(self):
        """测试缓存键前缀"""
        assert CACHE_KEY_PREFIX == "model:provider_configs"

    def test_cache_ttl(self):
        """测试缓存 TTL"""
        assert CACHE_TTL == 300  # 5 分钟


class TestProviderManagerGetDefaultProviderModelName:
    """ProviderManager get_default_provider_model_name 测试"""

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name(self):
        """测试获取默认提供者和模型名称"""
        manager = ProviderManager()

        # 模拟配置
        mock_configuration = MagicMock()
        mock_configuration.is_custom_configuration_available = MagicMock(
            return_value=True
        )
        mock_configuration.get_current_credentials = MagicMock(
            return_value={"api_key": "test"}
        )

        mock_configurations = MagicMock()
        mock_configurations.values = MagicMock(
            return_value=[mock_configuration]
        )

        manager.get_configurations = AsyncMock(return_value=mock_configurations)

        # 模拟 _get_first_provider_first_model
        manager._get_first_provider_first_model = AsyncMock(
            return_value=("openai", "gpt-4")
        )

        provider, model = await manager.get_default_provider_model_name(
            tenant_id="test-tenant",
            model_type=ModelType.LLM,
        )

        assert provider == "openai"
        assert model == "gpt-4"


class TestProviderManagerTenantIsolation:
    """ProviderManager 租户隔离测试"""

    @pytest.mark.asyncio
    async def test_configurations_isolated_by_tenant(self):
        """测试配置按租户隔离"""
        manager = ProviderManager()

        tenant1 = "tenant-001"
        tenant2 = "tenant-002"

        # 模拟两个租户的不同配置
        with patch(
            "ai.components.model.internal.provider_manager.get_cache_manager"
        ) as mock_get_cache:
            mock_cache_manager = AsyncMock()
            # 两个租户都缓存未命中
            mock_cache_manager.get = AsyncMock(return_value=None)
            mock_get_cache.return_value = mock_cache_manager

            # 需要完整模拟配置加载流程
            manager._get_all_providers = AsyncMock(return_value={})
            manager._get_all_provider_model_settings = AsyncMock(return_value={})
            manager._get_all_custom_models = AsyncMock(return_value={})

            with patch(
                "ai.components.model.internal.provider_manager.ModelProviderFactory"
            ) as mock_factory_class:
                mock_factory = MagicMock()
                mock_factory.get_providers = AsyncMock(return_value=[])
                mock_factory_class.return_value = mock_factory

                with patch(
                    "ai.components.model.internal.provider_manager.ProviderConfigurations"
                ) as mock_configs_class:
                    mock_configs_class.return_value = MagicMock()

                    await manager.get_configurations(tenant1)
                    await manager.get_configurations(tenant2)

                    # 验证缓存键不同
                    calls = mock_cache_manager.get.call_args_list
                    tenant_keys = [call[0][0] for call in calls]
                    assert f"{CACHE_KEY_PREFIX}:{tenant1}" in tenant_keys
                    assert f"{CACHE_KEY_PREFIX}:{tenant2}" in tenant_keys
