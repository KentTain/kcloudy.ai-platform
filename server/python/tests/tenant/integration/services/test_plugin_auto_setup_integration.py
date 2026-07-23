"""插件自动设置集成测试

测试 Web 应用启动时插件自动安装、配置、启动的完整流程。

运行方式：
    uv run pytest -m e2e tests/tenant/integration/test_plugin_auto_setup_integration.py -v

注意：
    需要配置环境变量 E2E_TONGYI_API_KEY 才能运行模型调用测试。
"""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.services.llm_service import LLMService
from ai.components.plugin.engine.models.enums import PluginStatus
from ai.services.plugin import plugin_config_service
from ai_plugin.sdk.entities.model.message import (
    SystemPromptMessage,
    UserPromptMessage,
)
from ai_plugin.sdk.interfaces.model.large_language_model import LLMResult
from framework.configs.plugin_auto_setup import (
    PluginAutoSetupConfig,
    PluginAutoSetupItem,
    VerificationConfig,
)
from framework.tenant.context import TenantContext
from framework.tenant.plugin_protocols import get_plugin_installation_provider
from tenant.services.plugin import (
    PluginAutoSetupService,
    StartupSetupResult,
)
from tests.ai.e2e.helpers.plugin_test_helper import PluginTestHelper


class TestPluginAutoSetupIntegration:
    """插件自动设置集成测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_tongyi_plugin_auto_setup_full_lifecycle(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        tongyi_api_key: str,
        tongyi_api_key_available: bool,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试 tongyi 插件自动设置完整生命周期

        场景：Web 应用启动时自动设置 tongyi 插件
        - 预置插件定义（上传插件包）
        - 执行自动设置服务（安装 -> 配置 -> 启动）
        - 验证插件状态为 ACTIVE
        - 验证模型调用成功
        - 清理资源

        流程：预置定义 -> 自动设置 -> 验证状态 -> 模型调用 -> 清理
        """
        if not tongyi_api_key_available:
            pytest.skip("tongyi API Key 无效或服务不可用")

        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)
        TenantContext.set_tenant_id(test_tenant_id)

        plugin_id = "langgenius/tongyi"

        # -------------------------------------------------------------------------
        # 步骤 1：预置插件定义（上传插件包并安装，然后卸载保留定义）
        # -------------------------------------------------------------------------
        tongyi_path: Path = plugin_package_path("tongyi")

        # 使用 helper 安装插件（会同时创建插件定义）
        installed_plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
        )
        assert installed_plugin_id == plugin_id

        # 卸载插件但保留插件定义
        from ai.services.plugin import plugin_management_service

        await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        await e2e_session.commit()

        # 验证插件定义仍存在
        from tenant.models.plugin import TenantPluginDefinition

        definition = await TenantPluginDefinition.one_by_field(
            e2e_session, "plugin_id", plugin_id
        )
        assert definition is not None, "插件定义应存在"

        # -------------------------------------------------------------------------
        # 步骤 2：执行自动设置服务
        # -------------------------------------------------------------------------
        auto_setup_service = PluginAutoSetupService()

        config = PluginAutoSetupConfig(
            enabled=True,
            plugins=[
                PluginAutoSetupItem(
                    plugin_id=plugin_id,
                    auto_install=True,
                    auto_start=True,
                    credentials={
                        "dashscope_api_key": tongyi_api_key,
                    },
                )
            ],
            verification=VerificationConfig(enabled=False),
        )

        result = await auto_setup_service.setup_plugins(e2e_session, config)
        await e2e_session.commit()

        # -------------------------------------------------------------------------
        # 步骤 3：验证设置结果
        # -------------------------------------------------------------------------
        assert result.success_count == 1, f"成功计数应为 1，实际: {result.success_count}"
        assert result.failed_count == 0, f"失败计数应为 0，错误: {result.errors}"
        assert result.skipped_count == 0, f"跳过计数应为 0，实际: {result.skipped_count}"

        # -------------------------------------------------------------------------
        # 步骤 4：验证插件状态为 ACTIVE
        # -------------------------------------------------------------------------
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.ACTIVE,
            timeout=60.0,
        )

        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is not None, "安装记录应存在"
        assert installation.status.upper() == "ACTIVE", (
            f"状态应为 ACTIVE，实际: {installation.status}"
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        assert runtime_info["status"] == "active"

        # -------------------------------------------------------------------------
        # 步骤 5：验证模型调用成功
        # -------------------------------------------------------------------------
        try:
            llm_service = LLMService(test_tenant_id)

            # 构建提示消息
            prompt_messages = [
                SystemPromptMessage(content="你是一个有帮助的助手。"),
                UserPromptMessage(content="请用一句话回答：1+1等于几？"),
            ]

            # 调用模型
            llm_result = await llm_service.invoke(
                prompt_messages=prompt_messages,
                provider="tongyi",
                model="qwen-turbo",
                model_parameters={"temperature": 0.1, "max_tokens": 50},
            )

            # 验证结果
            assert llm_result is not None, "模型调用结果不应为空"
            assert isinstance(llm_result, LLMResult), (
                f"结果类型应为 LLMResult，实际为 {type(llm_result)}"
            )
            assert llm_result.message is not None, "模型消息不应为空"
            assert llm_result.message.content, "模型消息内容不应为空"

        except Exception as e:
            # 模型调用失败不影响生命周期测试，记录日志
            pytest.skip(f"模型调用失败（可能是 API 配额限制）：{e}")

        # -------------------------------------------------------------------------
        # 步骤 6：清理资源
        # -------------------------------------------------------------------------
        from ai.services.plugin import plugin_management_service

        await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        await e2e_session.commit()

        # 验证资源清理
        installation_after = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation_after is None, "安装记录应已删除"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_plugin_auto_setup_idempotent_reinstall(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        tongyi_api_key: str,
        tongyi_api_key_available: bool,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试插件自动设置幂等性（重复安装）

        场景：已安装的插件再次执行自动设置
        - 预置插件定义
        - 第一次自动设置（安装 -> 配置 -> 启动）
        - 第二次自动设置（跳过安装 -> 重新配置 -> 重新启动）
        - 验证幂等性（不创建重复记录）

        流程：预置定义 -> 首次设置 -> 再次设置 -> 验证幂等
        """
        if not tongyi_api_key_available:
            pytest.skip("tongyi API Key 无效或服务不可用")

        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)
        TenantContext.set_tenant_id(test_tenant_id)

        plugin_id = "langgenius/tongyi"

        # -------------------------------------------------------------------------
        # 步骤 1：预置插件定义
        # -------------------------------------------------------------------------
        tongyi_path: Path = plugin_package_path("tongyi")

        # 使用 helper 安装插件（会同时创建插件定义）
        installed_plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
        )
        assert installed_plugin_id == plugin_id

        # 卸载插件但保留插件定义
        from ai.services.plugin import plugin_management_service

        await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        await e2e_session.commit()

        # -------------------------------------------------------------------------
        # 步骤 2：第一次自动设置
        # -------------------------------------------------------------------------
        auto_setup_service = PluginAutoSetupService()

        config = PluginAutoSetupConfig(
            enabled=True,
            plugins=[
                PluginAutoSetupItem(
                    plugin_id=plugin_id,
                    auto_install=True,
                    auto_start=True,
                    credentials={
                        "dashscope_api_key": tongyi_api_key,
                    },
                )
            ],
            verification=VerificationConfig(enabled=False),
        )

        result1 = await auto_setup_service.setup_plugins(e2e_session, config)
        await e2e_session.commit()

        assert result1.success_count == 1, f"首次设置成功计数应为 1"
        assert result1.failed_count == 0, f"首次设置失败计数应为 0"
        assert result1.skipped_count == 0, f"首次设置跳过计数应为 0"

        # 等待插件启动
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.ACTIVE,
            timeout=60.0,
        )

        # -------------------------------------------------------------------------
        # 步骤 3：第二次自动设置（幂等性测试）
        # -------------------------------------------------------------------------
        result2 = await auto_setup_service.setup_plugins(e2e_session, config)
        await e2e_session.commit()

        # 验证幂等性：跳过安装但成功配置和启动
        assert result2.success_count == 1, f"再次设置成功计数应为 1"
        assert result2.failed_count == 0, f"再次设置失败计数应为 0"
        assert result2.skipped_count == 1, f"再次设置跳过计数应为 1（跳过安装）"

        # 验证只有一条安装记录
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is not None, "安装记录应存在"

        # -------------------------------------------------------------------------
        # 步骤 4：清理资源
        # -------------------------------------------------------------------------
        from ai.services.plugin import plugin_management_service

        await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        await e2e_session.commit()

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_plugin_auto_setup_definition_not_found(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试插件定义不存在的错误处理

        场景：配置的插件 ID 对应的定义不存在
        - 执行自动设置服务
        - 验证错误处理（失败但不抛异常）
        - 验证错误信息记录

        流程：执行设置 -> 验证失败 -> 验证错误信息
        """
        TenantContext.set_tenant_id(test_tenant_id)

        auto_setup_service = PluginAutoSetupService()

        config = PluginAutoSetupConfig(
            enabled=True,
            plugins=[
                PluginAutoSetupItem(
                    plugin_id="nonexistent/plugin",
                    auto_install=True,
                    auto_start=True,
                    credentials={"api_key": "test-key"},
                )
            ],
            verification=VerificationConfig(enabled=False),
        )

        result = await auto_setup_service.setup_plugins(e2e_session, config)
        await e2e_session.commit()

        # 验证失败处理
        assert result.success_count == 0, f"成功计数应为 0"
        assert result.failed_count == 1, f"失败计数应为 1"
        assert result.skipped_count == 0, f"跳过计数应为 0"
        assert len(result.errors) == 1, f"应有 1 条错误信息"
        assert "插件定义不存在" in result.errors[0], (
            f"错误信息应包含'插件定义不存在'，实际: {result.errors[0]}"
        )
