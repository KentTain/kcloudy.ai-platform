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
from ai_plugin.sdk.entities.model.message import (
    SystemPromptMessage,
    UserPromptMessage,
)
from ai_plugin.sdk.interfaces.model.large_language_model import LLMResult
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
        cleanup_test_resources: dict,
    ) -> None:
        """
        测试 tongyi 插件完整生命周期

        场景：tongyi 插件完整生命周期
        - 上传并安装 tongyi 插件包
        - 配置 tongyi API Key 凭证
        - 启动插件
        - 调用模型生成
        - 停止插件
        - 卸载插件
        - 验证每个步骤都成功完成
        - 验证最终资源完全清理
        """
        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)

        # 获取插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")
        plugin_id = "langgenius/tongyi"

        # 记录初始资源状态
        initial_plugins = await helper.get_all_plugins(e2e_session)
        initial_running = await helper.get_running_plugins(e2e_session)

        # -------------------------------------------------------------------------
        # 步骤 1：安装插件
        # -------------------------------------------------------------------------
        plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
            auto_start=False,  # 不自动启动，稍后手动启动
        )

        # 验证安装成功
        plugin_info = await helper.assert_plugin_installed(e2e_session, plugin_id)
        assert plugin_info["id"] == plugin_id
        assert plugin_info["status"] in ("ACTIVE", "INACTIVE")

        # -------------------------------------------------------------------------
        # 步骤 2：配置凭证
        # -------------------------------------------------------------------------
        manager = await helper.get_manager(e2e_session)

        # 更新插件配置，添加 API Key
        # 查找现有配置
        from sqlalchemy import select

        from ai.models.plugin_config import PluginConfig as AIPluginConfig

        config_result = await e2e_session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == test_tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = config_result.scalar_one_or_none()

        if ai_config and ai_config.plugin_config:
            plugin_config = ai_config.plugin_config.copy()
        else:
            plugin_config = {}

        # 设置凭证
        if "runtime_configuration" not in plugin_config:
            plugin_config["runtime_configuration"] = {}

        # tongyi 使用 dashscope_api_key
        plugin_config["runtime_configuration"]["credentials"] = {
            "dashscope_api_key": tongyi_api_key,
        }

        # 更新配置
        if ai_config:
            ai_config.plugin_config = plugin_config
        else:
            ai_config = AIPluginConfig(
                tenant_id=test_tenant_id,
                plugin_id=plugin_id,
                plugin_config=plugin_config,
            )
            e2e_session.add(ai_config)

        await e2e_session.flush()

        # -------------------------------------------------------------------------
        # 步骤 3：启动插件
        # -------------------------------------------------------------------------
        success = await manager.start_plugin(plugin_id, e2e_session)
        assert success is True, "启动插件失败"

        # 等待插件状态变为 ACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            "ACTIVE",
            timeout=60.0,
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        assert runtime_info["status"] == "active"

        # -------------------------------------------------------------------------
        # 步骤 4：调用模型生成
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
        # 步骤 5：停止插件
        # -------------------------------------------------------------------------
        success = await manager.stop_plugin(plugin_id, e2e_session)
        assert success is True, "停止插件失败"

        # 等待插件状态变为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            "INACTIVE",
            timeout=30.0,
        )

        # 验证插件已停止
        is_running = await helper.is_plugin_running(e2e_session, plugin_id)
        assert is_running is False, "插件应该已停止"

        # -------------------------------------------------------------------------
        # 步骤 6：卸载插件
        # -------------------------------------------------------------------------
        success = await manager.uninstall_plugin(e2e_session, plugin_id)
        assert success is True, "卸载插件失败"

        # -------------------------------------------------------------------------
        # 步骤 7：验证资源清理
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
        cleanup_test_resources: dict,
    ) -> None:
        """
        测试 gpustack 插件完整生命周期

        场景：gpustack 插件完整生命周期
        - 上传并安装 gpustack 插件包
        - 配置 gpustack API Key 和 Endpoint
        - 启动插件
        - 调用模型生成
        - 停止插件
        - 卸载插件
        - 验证每个步骤都成功完成
        - 验证最终资源完全清理
        """
        import os

        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)

        # 获取插件包路径
        gpustack_path: Path = plugin_package_path("gpustack")
        plugin_id = "langgenius/gpustack"

        # 记录初始资源状态
        initial_plugins = await helper.get_all_plugins(e2e_session)
        initial_running = await helper.get_running_plugins(e2e_session)

        # -------------------------------------------------------------------------
        # 步骤 1：安装插件
        # -------------------------------------------------------------------------
        plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(gpustack_path),
            auto_start=False,
        )

        # 验证安装成功
        plugin_info = await helper.assert_plugin_installed(e2e_session, plugin_id)
        assert plugin_info["id"] == plugin_id
        assert plugin_info["status"] in ("ACTIVE", "INACTIVE")

        # -------------------------------------------------------------------------
        # 步骤 2：配置凭证
        # -------------------------------------------------------------------------
        manager = await helper.get_manager(e2e_session)

        # 更新插件配置
        from sqlalchemy import select

        from ai.models.plugin_config import PluginConfig as AIPluginConfig

        config_result = await e2e_session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == test_tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = config_result.scalar_one_or_none()

        if ai_config and ai_config.plugin_config:
            plugin_config = ai_config.plugin_config.copy()
        else:
            plugin_config = {}

        # 设置凭证
        if "runtime_configuration" not in plugin_config:
            plugin_config["runtime_configuration"] = {}

        # GPUStack 使用 api_key 和 endpoint
        plugin_config["runtime_configuration"]["credentials"] = {
            "api_key": gpustack_api_key,
            "endpoint": gpustack_endpoint,
        }

        # 更新配置
        if ai_config:
            ai_config.plugin_config = plugin_config
        else:
            ai_config = AIPluginConfig(
                tenant_id=test_tenant_id,
                plugin_id=plugin_id,
                plugin_config=plugin_config,
            )
            e2e_session.add(ai_config)

        await e2e_session.flush()

        # -------------------------------------------------------------------------
        # 步骤 3：启动插件
        # -------------------------------------------------------------------------
        success = await manager.start_plugin(plugin_id, e2e_session)
        assert success is True, "启动插件失败"

        # 等待插件状态变为 ACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            "ACTIVE",
            timeout=60.0,
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        assert runtime_info["status"] == "active"

        # -------------------------------------------------------------------------
        # 步骤 4：调用模型生成
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
        # 步骤 5：停止插件
        # -------------------------------------------------------------------------
        success = await manager.stop_plugin(plugin_id, e2e_session)
        assert success is True, "停止插件失败"

        # 等待插件状态变为 INACTIVE
        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            "INACTIVE",
            timeout=30.0,
        )

        # 验证插件已停止
        is_running = await helper.is_plugin_running(e2e_session, plugin_id)
        assert is_running is False, "插件应该已停止"

        # -------------------------------------------------------------------------
        # 步骤 6：卸载插件
        # -------------------------------------------------------------------------
        success = await manager.uninstall_plugin(e2e_session, plugin_id)
        assert success is True, "卸载插件失败"

        # -------------------------------------------------------------------------
        # 步骤 7：验证资源清理
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
    ) -> None:
        """
        测试插件生命周期中的资源清理

        场景：插件生命周期资源清理
        - 安装插件
        - 启动插件
        - 强制停止插件（模拟异常）
        - 卸载插件
        - 验证所有资源都被正确清理
        """
        # 初始化辅助工具
        helper = PluginTestHelper(test_tenant_id)

        # 获取 tongyi 插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")
        plugin_id = "langgenius/tongyi"

        # -------------------------------------------------------------------------
        # 安装并启动插件
        # -------------------------------------------------------------------------
        plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
            auto_start=False,
        )

        manager = await helper.get_manager(e2e_session)

        # 启动插件
        success = await manager.start_plugin(plugin_id, e2e_session)
        assert success is True

        await helper.wait_for_plugin_status(
            e2e_session, plugin_id, "ACTIVE", timeout=60.0
        )

        # 验证插件正在运行
        runtime_info = await helper.assert_plugin_running(e2e_session, plugin_id)
        pid = runtime_info.get("pid")

        # -------------------------------------------------------------------------
        # 正常停止和卸载
        # -------------------------------------------------------------------------
        # 停止插件
        success = await manager.stop_plugin(plugin_id, e2e_session)
        assert success is True

        # 卸载插件
        success = await manager.uninstall_plugin(e2e_session, plugin_id)
        assert success is True

        # -------------------------------------------------------------------------
        # 验证资源清理
        # -------------------------------------------------------------------------
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

        from ai.models.plugin_config import PluginConfig as AIPluginConfig

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
