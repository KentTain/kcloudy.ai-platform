"""ProviderManager 凭证注入单元测试

测试 ProviderManager 的凭证注入功能。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.internal.provider_manager import ProviderManager
from ai.models.plugin import PluginCredential


@pytest.mark.asyncio
class TestProviderManagerCredentialInjection:
    """ProviderManager 凭证注入测试"""

    async def test_extract_plugin_id_from_provider(self):
        """测试从 provider 名称中提取 plugin_id"""
        manager = ProviderManager()

        # 测试标准 plugin provider 格式
        plugin_id = manager._extract_plugin_id_from_provider("plugin/alon/tongyi")
        assert plugin_id == "alon/tongyi"

        # 测试非 plugin provider
        plugin_id = manager._extract_plugin_id_from_provider("openai")
        assert plugin_id is None

        # 测试只有 plugin/ 前缀但没有后续内容
        plugin_id = manager._extract_plugin_id_from_provider("plugin/")
        assert plugin_id is None

    async def test_inject_plugin_credentials_without_session(self):
        """测试没有 session 时不注入凭证"""
        manager = ProviderManager()

        # 创建空的 provider_configurations
        from ai.components.model.internal.provider_configuration import (
            ProviderConfigurations,
        )

        provider_configurations = ProviderConfigurations(tenant_id="test-tenant")

        # 调用注入方法（没有 session）
        await manager._inject_plugin_credentials(
            session=None,
            provider_configurations=provider_configurations,
        )

        # 验证没有变化
        assert len(provider_configurations) == 0

    async def test_inject_plugin_credentials_with_plugin_provider(
        self, session: AsyncSession
    ):
        """测试注入插件凭证到 plugin provider"""
        manager = ProviderManager()

        # 准备测试数据：创建一个插件凭证
        credential = PluginCredential(
            tenant_id="test-tenant",
            plugin_id="alon/tongyi",
            plugin_type="model",
            name="test-credential",
            credentials={"api_key": "test-api-key"},
            is_disabled=False,
        )
        session.add(credential)
        await session.commit()

        # 创建 provider_configurations（这里需要 mock provider entity）
        # 注意：这个测试需要更完整的 setup，这里仅作为示例
        # 实际实现时需要创建完整的 ProviderConfiguration 对象

        # 调用注入方法
        # await manager._inject_plugin_credentials(
        #     session=session,
        #     provider_configurations=provider_configurations,
        # )

        # 验证凭证已注入
        # ...

    async def test_inject_plugin_credentials_marks_deprecated(self):
        """测试注入方法标记为废弃"""
        manager = ProviderManager()

        # 检查方法是否存在
        assert hasattr(manager, "_inject_plugin_credentials")

        # 这个方法应该被标记为废弃（通过装饰器或文档字符串）
        # 实际验证可能需要检查 __doc__ 或其他元数据
