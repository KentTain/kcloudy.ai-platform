"""插件验证服务测试"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from framework.configs.plugin_auto_setup import VerificationConfig
from framework.tenant.context import TenantContext
from ai.services.plugin_verification_service import PluginVerificationService


@pytest.fixture
def verification_service():
    """验证服务实例"""
    return PluginVerificationService()


@pytest.fixture
def verification_config():
    """验证配置"""
    return VerificationConfig(enabled=True, timeout=10, on_failure="warn")


@pytest.fixture(autouse=True)
def tenant_context():
    """设置租户上下文"""
    TenantContext.set_tenant_id("test-tenant")
    yield
    TenantContext.clear()


def _mock_task_session():
    """创建 mock get_task_session 上下文管理器"""
    mock_session = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm


@pytest.mark.asyncio
async def test_verify_all_plugins_empty_list(verification_service):
    """测试空插件列表"""
    results = await verification_service.verify_all_plugins([], VerificationConfig())
    assert results == {}


@pytest.mark.asyncio
async def test_verify_all_plugins_success(verification_service, verification_config):
    """测试验证成功"""
    plugin_ids = ["langgenius-tongyi", "langgenius-gpustack"]

    with patch.object(
        verification_service,
        "_verify_single_plugin",
        return_value=True,
    ):
        results = await verification_service.verify_all_plugins(
            plugin_ids, verification_config
        )

    assert len(results) == 2
    assert all(results.values())


@pytest.mark.asyncio
async def test_verify_all_plugins_partial_failure(verification_service, verification_config):
    """测试部分验证失败"""
    plugin_ids = ["langgenius-tongyi", "langgenius-gpustack"]

    async def mock_verify(plugin_id: str, timeout: int) -> bool:
        return plugin_id == "langgenius-tongyi"

    with patch.object(
        verification_service,
        "_verify_single_plugin",
        side_effect=mock_verify,
    ):
        results = await verification_service.verify_all_plugins(
            plugin_ids, verification_config
        )

    assert results["langgenius-tongyi"] is True
    assert results["langgenius-gpustack"] is False


@pytest.mark.asyncio
async def test_handle_verification_failure_warn(verification_service):
    """测试验证失败策略：warn"""
    with patch("ai.services.plugin_verification_service._logger") as mock_logger:
        await verification_service.handle_verification_failure(
            "langgenius-gpustack", "warn"
        )
        mock_logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_handle_verification_failure_degrade(verification_service):
    """测试验证失败策略：degrade"""
    with patch.object(
        verification_service,
        "_update_runtime_state",
        new_callable=AsyncMock,
    ) as mock_update:
        await verification_service.handle_verification_failure(
            "langgenius-gpustack", "degrade"
        )
        mock_update.assert_called_once_with("langgenius-gpustack", "DEGRADED")


@pytest.mark.asyncio
async def test_handle_verification_failure_fail(verification_service):
    """测试验证失败策略：fail"""
    with patch("ai.services.plugin_verification_service._logger") as mock_logger:
        await verification_service.handle_verification_failure(
            "langgenius-gpustack", "fail"
        )
        mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_verify_single_plugin_delegates_to_test_plugin(verification_service):
    """测试 _verify_single_plugin 委托给 plugin_config_service.test_plugin"""
    mock_response = MagicMock()
    mock_response.validated = True

    with patch(
        "ai.services.plugin_verification_service.get_task_session",
        return_value=_mock_task_session(),
    ), patch(
        "ai.services.plugin_verification_service.plugin_config_service.test_plugin",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await verification_service._verify_single_plugin("langgenius-tongyi", 10)

    assert result is True


@pytest.mark.asyncio
async def test_verify_single_plugin_timeout(verification_service):
    """测试验证超时"""
    with patch(
        "ai.services.plugin_verification_service.get_task_session",
        return_value=_mock_task_session(),
    ), patch(
        "ai.services.plugin_verification_service.asyncio.wait_for",
        side_effect=asyncio.TimeoutError(),
    ):
        result = await verification_service._verify_single_plugin("langgenius-tongyi", 1)

    assert result is False


@pytest.mark.asyncio
async def test_verify_single_plugin_exception(verification_service):
    """测试验证时抛出异常"""
    with patch(
        "ai.services.plugin_verification_service.get_task_session",
        return_value=_mock_task_session(),
    ), patch(
        "ai.services.plugin_verification_service.plugin_config_service.test_plugin",
        new=AsyncMock(side_effect=RuntimeError("test error")),
    ):
        result = await verification_service._verify_single_plugin("langgenius-tongyi", 10)

    assert result is False


@pytest.mark.asyncio
async def test_update_runtime_state_exists(verification_service):
    """测试更新运行时状态-记录存在"""
    mock_runtime = MagicMock()
    mock_runtime.status = "running"
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_model_cls = MagicMock()
    mock_model_cls.first_by_fields = AsyncMock(return_value=mock_runtime)

    with patch(
        "ai.services.plugin_verification_service.get_task_session",
        return_value=mock_cm,
    ), patch.dict(
        "sys.modules",
        {"ai.models.plugin_runtime_state": MagicMock(
            PluginRuntimeState=mock_model_cls
        )},
    ), patch(
        "ai.models.plugin_runtime_state.PluginRuntimeState",
        mock_model_cls,
        create=True,
    ):
        await verification_service._update_runtime_state("langgenius-tongyi", "DEGRADED")

    assert mock_runtime.status == "DEGRADED"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_runtime_state_not_exists(verification_service):
    """测试更新运行时状态-记录不存在"""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_model_cls = MagicMock()
    mock_model_cls.first_by_fields = AsyncMock(return_value=None)

    with patch(
        "ai.services.plugin_verification_service.get_task_session",
        return_value=mock_cm,
    ), patch(
        "ai.models.plugin_runtime_state.PluginRuntimeState",
        mock_model_cls,
        create=True,
    ):
        await verification_service._update_runtime_state("langgenius-tongyi", "DEGRADED")

    mock_session.commit.assert_not_awaited()
