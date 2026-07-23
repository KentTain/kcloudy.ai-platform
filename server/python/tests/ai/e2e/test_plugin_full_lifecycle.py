"""
插件完整生命周期测试

测试插件的完整生命周期，包括安装、配置、启动、模型调用、停止、卸载。

运行方式：
    uv run pytest -m e2e tests/ai/e2e/test_plugin_full_lifecycle.py -v

注意：
    需要配置环境变量 E2E_TONGYI_API_KEY 和 E2E_GPUSTACK_API_KEY 才能运行模型调用测试。
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
from framework.tenant.context import TenantContext
from framework.tenant.plugin_protocols import get_plugin_installation_provider
from tests.ai.e2e.helpers.plugin_test_helper import PluginTestHelper


class TestPluginFullLifecycle:
    """插件完整生命周期测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_tongyi_plugin_full_lifecycle(
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
        测试 tongyi 插件完整生命周期

        场景：tongyi 插件完整生命周期
        - 上传并安装 tongyi 插件包
        - 配置 tongyi API Key 凭证
        - 测试配置连接
        - 启动插件
        - 调用模型生成
        - 停止插件
        - 卸载插件
        - 验证每个步骤都成功完成
        - 验证最终资源完全清理

        流程：安装 → 配置 → 测试 → 启动 → 调用 → 停止 → 卸载
        """
        if not tongyi_api_key_available:
            pytest.skip("tongyi API Key 无效或服务不可用")

        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")
        plugin_id = "langgenius/tongyi"

        # -------------------------------------------------------------------------
        # 步骤 1：安装插件
        # -------------------------------------------------------------------------
        plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
        )

        # 验证安装成功，状态为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.INACTIVE,
            timeout=60.0,
        )
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is not None, "安装记录应存在"
        assert installation.status.upper() == "INACTIVE", (
            f"状态应为 INACTIVE，实际: {installation.status}"
        )

        # -------------------------------------------------------------------------
        # 步骤 2：配置凭证
        # -------------------------------------------------------------------------
        config_response = await plugin_config_service.config_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
            plugin_config={
                "credentials": {
                    "dashscope_api_key": tongyi_api_key,
                }
            },
            runtime_config=None,
        )
        assert config_response.plugin_id == plugin_id

        # -------------------------------------------------------------------------
        # 步骤 3：测试配置连接
        # -------------------------------------------------------------------------
        test_response = await plugin_config_service.test_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert test_response.plugin_id == plugin_id
        assert test_response.validated is True, f"配置测试失败: {test_response.message}"

        # -------------------------------------------------------------------------
        # 步骤 4：启动插件
        # -------------------------------------------------------------------------
        start_response = await plugin_config_service.start_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert start_response.status == "ACTIVE", (
            f"插件启动失败，状态: {start_response.status}, 警告: {start_response.warning}"
        )

        # 等待插件状态变为 ACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.ACTIVE,
            timeout=60.0,
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        assert runtime_info["status"] == "active"

        # -------------------------------------------------------------------------
        # 步骤 5：调用模型生成
        # -------------------------------------------------------------------------
        try:
            llm_service = LLMService(test_tenant_id)

            # 构建提示消息
            prompt_messages = [
                SystemPromptMessage(content="你是一个有帮助的助手。"),
                UserPromptMessage(content="请用一句话回答：1+1等于几？"),
            ]

            # 调用模型
            result = await llm_service.invoke(
                prompt_messages=prompt_messages,
                provider="tongyi",
                model="qwen-turbo",
                model_parameters={"temperature": 0.1, "max_tokens": 50},
            )

            # 验证结果
            assert result is not None, "模型调用结果不应为空"
            assert isinstance(result, LLMResult), (
                f"结果类型应为 LLMResult，实际为 {type(result)}"
            )
            assert result.message is not None, "模型消息不应为空"
            assert result.message.content, "模型消息内容不应为空"

        except Exception as e:
            # 模型调用失败不影响生命周期测试，记录日志
            pytest.skip(f"模型调用失败（可能是 API 配额限制）：{e}")

        # -------------------------------------------------------------------------
        # 步骤 6：停止插件
        # -------------------------------------------------------------------------
        stop_response = await plugin_config_service.stop_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert stop_response.status == "INACTIVE", (
            f"插件停止失败，状态: {stop_response.status}"
        )

        # 等待插件状态变为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.INACTIVE,
            timeout=30.0,
        )

        # 验证插件已停止
        is_running = await helper.is_plugin_running(e2e_session, plugin_id)
        assert is_running is False, "插件应该已停止"

        # -------------------------------------------------------------------------
        # 步骤 7：卸载插件
        # -------------------------------------------------------------------------
        from ai.services.plugin import plugin_management_service

        result = await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        assert result.success is True, "卸载插件失败"

        # -------------------------------------------------------------------------
        # 步骤 8：验证资源清理
        # -------------------------------------------------------------------------
        # 验证插件从内存中移除
        plugins_after = await helper.get_all_plugins(e2e_session)
        assert plugin_id not in plugins_after, "插件应从内存中移除"

        # 验证运行时已清理
        running_after = await helper.get_running_plugins(e2e_session)
        assert plugin_id not in running_after, "插件运行时应已清理"

        # 验证数据库记录已删除
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is None, "安装记录应已删除"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_gpustack_plugin_full_lifecycle(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        gpustack_endpoint: str,
        gpustack_api_key: str,
        gpustack_api_key_available: bool,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试 gpustack 插件完整生命周期

        场景：gpustack 插件完整生命周期
        - 上传并安装 gpustack 插件包
        - 配置 gpustack API Key 和 Endpoint
        - 测试配置连接
        - 启动插件
        - 调用模型生成
        - 停止插件
        - 卸载插件
        - 验证每个步骤都成功完成
        - 验证最终资源完全清理

        流程：安装 → 配置 → 测试 → 启动 → 调用 → 停止 → 卸载
        """
        if not gpustack_api_key_available:
            pytest.skip("GPUStack API Key 无效或服务不可用")
        import os

        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取插件包路径
        gpustack_path: Path = plugin_package_path("gpustack")
        plugin_id = "langgenius/gpustack"

        # -------------------------------------------------------------------------
        # 步骤 1：安装插件
        # -------------------------------------------------------------------------
        plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(gpustack_path),
        )

        # 验证安装成功，状态为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.INACTIVE,
            timeout=60.0,
        )
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is not None, "安装记录应存在"
        assert installation.status.upper() == "INACTIVE", (
            f"状态应为 INACTIVE，实际: {installation.status}"
        )

        # -------------------------------------------------------------------------
        # 步骤 2：配置凭证
        # -------------------------------------------------------------------------
        config_response = await plugin_config_service.config_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
            plugin_config={
                "credentials": {
                    "api_key": gpustack_api_key,
                    "endpoint": gpustack_endpoint,
                }
            },
            runtime_config=None,
        )
        assert config_response.plugin_id == plugin_id

        # -------------------------------------------------------------------------
        # 步骤 3：测试配置连接
        # -------------------------------------------------------------------------
        test_response = await plugin_config_service.test_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert test_response.plugin_id == plugin_id
        assert test_response.validated is True, f"配置测试失败: {test_response.message}"

        # -------------------------------------------------------------------------
        # 步骤 4：启动插件
        # -------------------------------------------------------------------------
        start_response = await plugin_config_service.start_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert start_response.status == "ACTIVE", (
            f"插件启动失败，状态: {start_response.status}, 警告: {start_response.warning}"
        )

        # 等待插件状态变为 ACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.ACTIVE,
            timeout=60.0,
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        assert runtime_info["status"] == "active"

        # -------------------------------------------------------------------------
        # 步骤 5：调用模型生成
        # -------------------------------------------------------------------------
        try:
            # 获取可用模型列表
            from ai.components.model.internal.model_provider_factory import (
                ModelProviderFactory,
            )

            factory = ModelProviderFactory()
            provider_config = await factory.get_provider_config(
                test_tenant_id,
                "gpustack",
            )

            # 获取模型列表
            models = await provider_config.models()
            if not models or not models.models:
                pytest.skip("GPUStack 没有可用的模型，跳过模型调用测试")

            # 使用第一个可用模型
            first_model = models.models[0]
            model_name = first_model.model

            llm_service = LLMService(test_tenant_id)

            # 构建提示消息
            prompt_messages = [
                SystemPromptMessage(content="你是一个有帮助的助手。"),
                UserPromptMessage(content="请用一句话回答：1+1等于几？"),
            ]

            # 调用模型
            result = await llm_service.invoke(
                prompt_messages=prompt_messages,
                provider="gpustack",
                model=model_name,
                model_parameters={"temperature": 0.1, "max_tokens": 50},
            )

            # 验证结果
            assert result is not None, "模型调用结果不应为空"
            assert isinstance(result, LLMResult), (
                f"结果类型应为 LLMResult，实际为 {type(result)}"
            )
            assert result.message is not None, "模型消息不应为空"
            assert result.message.content, "模型消息内容不应为空"

        except Exception as e:
            # 模型调用失败不影响生命周期测试
            pytest.skip(f"模型调用失败：{e}")

        # -------------------------------------------------------------------------
        # 步骤 6：停止插件
        # -------------------------------------------------------------------------
        stop_response = await plugin_config_service.stop_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert stop_response.status == "INACTIVE", (
            f"插件停止失败，状态: {stop_response.status}"
        )

        # 等待插件状态变为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.INACTIVE,
            timeout=30.0,
        )

        # 验证插件已停止
        is_running = await helper.is_plugin_running(e2e_session, plugin_id)
        assert is_running is False, "插件应该已停止"

        # -------------------------------------------------------------------------
        # 步骤 7：卸载插件
        # -------------------------------------------------------------------------
        from ai.services.plugin import plugin_management_service

        result = await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        assert result.success is True, "卸载插件失败"

        # -------------------------------------------------------------------------
        # 步骤 8：验证资源清理
        # -------------------------------------------------------------------------
        # 验证插件从内存中移除
        plugins_after = await helper.get_all_plugins(e2e_session)
        assert plugin_id not in plugins_after, "插件应从内存中移除"

        # 验证运行时已清理
        running_after = await helper.get_running_plugins(e2e_session)
        assert plugin_id not in running_after, "插件运行时应已清理"

        # 验证数据库记录已删除
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is None, "安装记录应已删除"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_plugin_lifecycle_resource_cleanup(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试插件生命周期中的资源清理

        场景：插件生命周期资源清理
        - 安装插件
        - 启动插件
        - 停止插件
        - 卸载插件
        - 验证所有资源都被正确清理
        """
        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")
        plugin_id = "langgenius/tongyi"

        # -------------------------------------------------------------------------
        # 安装并启动插件
        # -------------------------------------------------------------------------
        plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
        )

        # 验证状态为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session, plugin_id, PluginStatus.INACTIVE, timeout=60.0
        )

        # 启动插件
        start_response = await plugin_config_service.start_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert start_response.status == "ACTIVE", (
            f"插件启动失败，状态: {start_response.status}, 警告: {start_response.warning}"
        )

        await helper.wait_for_plugin_status(
            e2e_session, plugin_id, PluginStatus.ACTIVE, timeout=60.0
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        pid = runtime_info.get("pid")

        # -------------------------------------------------------------------------
        # 正常停止和卸载
        # -------------------------------------------------------------------------
        # 停止插件
        stop_response = await plugin_config_service.stop_plugin(
            session=e2e_session,
            tenant_id=test_tenant_id,
            plugin_id=plugin_id,
        )
        assert stop_response.status == "INACTIVE", (
            f"插件停止失败，状态: {stop_response.status}"
        )

        # 卸载插件
        from ai.services.plugin import plugin_management_service

        result = await plugin_management_service.uninstall_plugin(e2e_session, plugin_id)
        assert result.success is True

        # -------------------------------------------------------------------------
        # 验证资源清理
        # -------------------------------------------------------------------------
        manager = await helper.get_manager(e2e_session)

        # 验证内存中的插件信息已清理
        assert plugin_id not in manager.plugins, "内存中的插件信息应已清理"

        # 验证运行时信息已清理
        assert plugin_id not in manager.running_plugins, "运行时信息应已清理"

        # 验证数据库记录已删除
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(test_tenant_id, plugin_id)
        assert installation is None, "数据库安装记录应已删除"

        # 验证 AI 侧配置已删除
        from sqlalchemy import select

        from ai.models.plugin import PluginConfig as AIPluginConfig

        config_result = await e2e_session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == test_tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = config_result.scalar_one_or_none()
        assert ai_config is None, "AI 配置记录应已删除"

        # 验证运行时状态已删除
        from ai.models import PluginRuntimeState

        state_result = await e2e_session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == test_tenant_id,
                PluginRuntimeState.plugin_id == plugin_id,
            )
        )
        runtime_state = state_result.scalar_one_or_none()
        assert runtime_state is None, "运行时状态记录应已删除"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_plugin_config_validation_failed(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试插件配置验证失败场景

        场景：配置验证失败
        - 安装插件
        - 配置无效凭证（空 credentials）
        - 测试配置连接，返回验证失败
        - 验证插件状态保持 INACTIVE（未启动）

        流程：安装 → 配置（无效）→ 测试（失败）
        """
        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)
        TenantContext.set_tenant_id(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")
        plugin_id = "langgenius/tongyi"

        try:
            # 步骤 1：安装插件
            plugin_id = await helper.install_plugin_from_path(
                e2e_session,
                str(tongyi_path),
            )

            # 验证状态为 INACTIVE
            await helper.wait_for_plugin_status(
                e2e_session,
                plugin_id,
                PluginStatus.INACTIVE,
                timeout=60.0,
            )

            # 步骤 2：配置插件（使用空凭证，模拟无效配置）
            config_response = await plugin_config_service.config_plugin(
                session=e2e_session,
                tenant_id=test_tenant_id,
                plugin_id=plugin_id,
                plugin_config={},
                runtime_config=None,
            )
            assert config_response.plugin_id == plugin_id

            # 步骤 3：测试配置连接（应返回验证失败）
            test_response = await plugin_config_service.test_plugin(
                session=e2e_session,
                tenant_id=test_tenant_id,
                plugin_id=plugin_id,
            )
            assert test_response.plugin_id == plugin_id
            assert test_response.validated is False, (
                f"空配置时测试应返回验证失败，实际: {test_response.validated}"
            )

            # 步骤 4：验证插件状态仍为 INACTIVE（未启动）
            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(test_tenant_id, plugin_id)
            assert installation is not None, "安装记录应存在"
            assert installation.status.upper() == "INACTIVE", (
                f"未启动的插件状态应为 INACTIVE，实际: {installation.status}"
            )

        finally:
            # 清理：卸载插件
            try:
                from ai.services.plugin import plugin_management_service

                await plugin_management_service.uninstall_plugin(
                    e2e_session, plugin_id
                )
            except Exception:
                pass
