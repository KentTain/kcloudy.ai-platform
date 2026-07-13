"""
默认模型管理单元测试

直接测试 Service 层逻辑，不需要运行的 HTTP 服务。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.services.plugin_default_model_service import plugin_default_model_service
from ai.models.plugin_default_model import PluginDefaultModel


@pytest.fixture
def mock_session():
    """Mock 数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def tenant_id():
    """测试租户 ID"""
    return "test_tenant_123"


@pytest.mark.asyncio
class TestPluginDefaultModelService:
    """插件默认模型服务测试"""

    async def test_get_default_model_not_found(self, mock_session, tenant_id):
        """测试获取不存在的默认模型"""
        # Mock 数据库查询返回 None
        with patch.object(
            PluginDefaultModel, 'one_by_conditions', new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = None

            result = await plugin_default_model_service.get_default_model(
                mock_session, tenant_id, "llm"
            )

            assert result is None
            mock_query.assert_called_once()

    async def test_set_default_model_create_new(self, mock_session, tenant_id):
        """测试创建新的默认模型"""
        # Mock 不存在现有记录
        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            # Mock 创建操作
            with patch.object(
                PluginDefaultModel, 'create', new_callable=AsyncMock
            ) as mock_create:
                mock_model = MagicMock(spec=PluginDefaultModel)
                mock_model.tenant_id = tenant_id
                mock_model.model_type = "llm"
                mock_model.plugin_id = "openai"
                mock_model.model_name = "gpt-4o-mini"
                mock_create.return_value = mock_model

                result = await plugin_default_model_service.set_default_model(
                    session=mock_session,
                    tenant_id=tenant_id,
                    model_type="llm",
                    plugin_id="openai",
                    model_name="gpt-4o-mini",
                )

                assert result.tenant_id == tenant_id
                assert result.model_type == "llm"
                assert result.plugin_id == "openai"
                assert result.model_name == "gpt-4o-mini"
                mock_create.assert_called_once()

    async def test_set_default_model_update_existing(self, mock_session, tenant_id):
        """测试更新现有默认模型"""
        # Mock 现有记录
        existing_model = MagicMock(spec=PluginDefaultModel)
        existing_model.tenant_id = tenant_id
        existing_model.model_type = "llm"
        existing_model.plugin_id = "openai"
        existing_model.model_name = "gpt-3.5-turbo"

        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = existing_model

            result = await plugin_default_model_service.set_default_model(
                session=mock_session,
                tenant_id=tenant_id,
                model_type="llm",
                plugin_id="anthropic",
                model_name="claude-3-5-sonnet-20241022",
            )

            assert result.plugin_id == "anthropic"
            assert result.model_name == "claude-3-5-sonnet-20241022"
            # 验证字段被更新
            assert existing_model.plugin_id == "anthropic"
            assert existing_model.model_name == "claude-3-5-sonnet-20241022"

    async def test_set_default_model_with_credential(self, mock_session, tenant_id):
        """测试设置带凭证的默认模型"""
        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            with patch.object(
                PluginDefaultModel, 'create', new_callable=AsyncMock
            ) as mock_create:
                mock_model = MagicMock(spec=PluginDefaultModel)
                mock_model.credential_id = "cred_123"
                mock_model.custom_base_url = "https://api.custom.com/v1"
                mock_create.return_value = mock_model

                result = await plugin_default_model_service.set_default_model(
                    session=mock_session,
                    tenant_id=tenant_id,
                    model_type="llm",
                    plugin_id="openai",
                    model_name="gpt-4o",
                    credential_id="cred_123",
                    custom_base_url="https://api.custom.com/v1",
                )

                assert result.credential_id == "cred_123"
                assert result.custom_base_url == "https://api.custom.com/v1"
                mock_create.assert_called_once()

    async def test_clear_default_model(self, mock_session, tenant_id):
        """测试清除默认模型（软删除）"""
        existing_model = MagicMock(spec=PluginDefaultModel)
        existing_model.is_valid = True

        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = existing_model

            await plugin_default_model_service.clear_default_model(
                mock_session, tenant_id, "llm"
            )

            # 验证 is_valid 被设置为 False
            assert existing_model.is_valid is False

    async def test_clear_default_model_not_found(self, mock_session, tenant_id):
        """测试清除不存在的默认模型"""
        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            # 应该不抛出异常
            await plugin_default_model_service.clear_default_model(
                mock_session, tenant_id, "llm"
            )

    async def test_multiple_model_types(self, mock_session, tenant_id):
        """测试多种模型类型的默认模型"""
        model_types = ["llm", "text-embedding", "rerank"]

        for model_type in model_types:
            with patch.object(
                plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
            ) as mock_get:
                mock_get.return_value = None

                with patch.object(
                    PluginDefaultModel, 'create', new_callable=AsyncMock
                ) as mock_create:
                    mock_model = MagicMock(spec=PluginDefaultModel)
                    mock_model.model_type = model_type
                    mock_create.return_value = mock_model

                    result = await plugin_default_model_service.set_default_model(
                        session=mock_session,
                        tenant_id=tenant_id,
                        model_type=model_type,
                        plugin_id="test_provider",
                        model_name=f"test_model_{model_type}",
                    )

                    assert result.model_type == model_type


@pytest.mark.asyncio
class TestDefaultModelServiceIntegration:
    """默认模型服务集成测试"""

    async def test_upsert_behavior(self, mock_session, tenant_id):
        """测试 upsert 行为（先查询，后创建或更新）"""
        # 第一次调用：创建
        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            with patch.object(
                PluginDefaultModel, 'create', new_callable=AsyncMock
            ) as mock_create:
                mock_model = MagicMock(spec=PluginDefaultModel)
                mock_create.return_value = mock_model

                await plugin_default_model_service.set_default_model(
                    session=mock_session,
                    tenant_id=tenant_id,
                    model_type="llm",
                    plugin_id="openai",
                    model_name="gpt-4o-mini",
                )

                mock_create.assert_called_once()

        # 第二次调用：更新
        existing_model = MagicMock(spec=PluginDefaultModel)
        existing_model.plugin_id = "openai"
        existing_model.model_name = "gpt-4o-mini"

        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = existing_model

            result = await plugin_default_model_service.set_default_model(
                session=mock_session,
                tenant_id=tenant_id,
                model_type="llm",
                plugin_id="anthropic",
                model_name="claude-3-5-sonnet-20241022",
            )

            # 验证更新而不是创建
            assert existing_model.plugin_id == "anthropic"
            assert existing_model.model_name == "claude-3-5-sonnet-20241022"

    async def test_tenant_isolation(self, mock_session):
        """测试租户隔离"""
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"

        # 为租户 1 创建默认模型
        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            with patch.object(
                PluginDefaultModel, 'create', new_callable=AsyncMock
            ) as mock_create:
                mock_model1 = MagicMock(spec=PluginDefaultModel)
                mock_model1.tenant_id = tenant1
                mock_create.return_value = mock_model1

                result1 = await plugin_default_model_service.set_default_model(
                    session=mock_session,
                    tenant_id=tenant1,
                    model_type="llm",
                    plugin_id="openai",
                    model_name="gpt-4o-mini",
                )

                # 验证传入的 tenant_id 正确
                call_args = mock_create.call_args
                assert call_args[1]['tenant_id'] == tenant1

        # 为租户 2 创建默认模型
        with patch.object(
            plugin_default_model_service, 'get_default_model', new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            with patch.object(
                PluginDefaultModel, 'create', new_callable=AsyncMock
            ) as mock_create:
                mock_model2 = MagicMock(spec=PluginDefaultModel)
                mock_model2.tenant_id = tenant2
                mock_create.return_value = mock_model2

                result2 = await plugin_default_model_service.set_default_model(
                    session=mock_session,
                    tenant_id=tenant2,
                    model_type="llm",
                    plugin_id="anthropic",
                    model_name="claude-3-5-sonnet-20241022",
                )

                # 验证传入的 tenant_id 正确
                call_args = mock_create.call_args
                assert call_args[1]['tenant_id'] == tenant2
