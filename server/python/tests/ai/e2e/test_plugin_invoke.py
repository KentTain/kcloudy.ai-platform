"""
模型调用测试

测试插件的模型调用功能，包括：
- 调用 tongyi 模型并验证响应
- 调用 gpustack 模型并验证响应
- 流式调用 tongyi 模型并验证增量响应
- 无效 API Key 调用验证错误处理

运行方式：
    # 运行所有 E2E 测试
    uv run pytest -m e2e tests/ai/e2e/test_plugin_invoke.py -v

注意：
    此测试需要真实 API Key，会产生费用。
    tongyi 测试需要配置环境变量 E2E_TONGYI_API_KEY（未配置则跳过）
    gpustack 测试优先使用环境变量 E2E_GPUSTACK_API_KEY 和 E2E_GPUSTACK_ENDPOINT，未配置则使用默认测试配置
"""

from __future__ import annotations

import os
import platform
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory
from ai.components.plugin.engine.models.enums import PluginStatus
from ai.components.plugin.engine.models.request import InstallRequest
from ai_plugin.sdk.entities.model.message import UserPromptMessage
from framework.tenant.plugin_protocols import get_plugin_installation_provider

from tests.ai.e2e.helpers.plugin_test_helper import PluginTestHelper

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Windows 上 gevent.os.tp_read 无法读取 asyncio 子进程 stdin 管道，
# 导致插件进程收不到请求而超时。Linux 上正常。
IS_WINDOWS = platform.system() == "Windows"


@pytest.mark.skipif(
    IS_WINDOWS,
    reason="Windows 上 gevent.os.tp_read 无法读取 asyncio 子进程 stdin 管道，"
    "导致插件调用超时。Linux 上正常。"
    "详见：gevent + ProactorEventLoop 管道兼容性",
)
class TestPluginInvokeTongyi:
    """tongyi 插件模型调用测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invoke_tongyi_model(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        tongyi_api_key: str,
        tongyi_api_key_available: bool,
        plugin_provider,
    ) -> None:
        """
        测试调用 tongyi 模型并验证响应

        场景：调用 tongyi 模型
        - 配置有效的 tongyi API Key
        - 调用模型生成接口
        - 系统成功调用 tongyi API
        - 返回有效的模型响应
        """
        if not tongyi_api_key_available:
            pytest.skip("tongyi API Key 无效或服务不可用")

        plugin_id = "langgenius/tongyi"
        helper = PluginTestHelper(tenant_id=test_tenant_id)

        try:
            # 1. 安装并启动插件
            package_path: Path = plugin_package_path("tongyi")
            installed_plugin_id = await helper.install_plugin_from_path(
                session=e2e_session,
                package_path=str(package_path),
                auto_start=True,
            )
            assert installed_plugin_id == plugin_id, (
                f"插件 ID 应为 '{plugin_id}'，实际为 '{installed_plugin_id}'"
            )

            # 2. 等待插件状态为 ACTIVE
            await helper.wait_for_plugin_status(
                session=e2e_session,
                plugin_id=plugin_id,
                target_status=PluginStatus.ACTIVE,
                timeout=30.0,
            )

            # 3. 调用 tongyi 模型
            manager = await helper.get_manager(e2e_session)

            # 构造模型调用请求
            invoke_request = {
                "type": "model",
                "action": "invoke_llm",
                "user_id": f"{test_tenant_id}-user",
                "provider": "tongyi",
                "model_type": "llm",
                "model": "qwen-plus",
                "credentials": {
                    "dashscope_api_key": tongyi_api_key,
                },
                "prompt_messages": [
                    {
                        "role": "user",
                        "content": "你好，请用一句话介绍你自己。",
                    }
                ],
                "model_parameters": {
                    "temperature": 0.7,
                    "max_tokens": 100,
                },
                "stream": True,
                "tools": None,
                "stop": None,
            }

            # 流式调用并收集响应
            chunks = []
            async for chunk in manager.invoke_plugin_stream(
                e2e_session, plugin_id, invoke_request, timeout=60
            ):
                chunks.append(chunk)

            # 4. 验证响应
            assert len(chunks) > 0, "应收到至少一个响应块"

            # 验证响应内容（chunk 结构：{"type": "stream", "data": {"delta": {...}}})
            has_content = False
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                data = chunk.get("data") or chunk
                if isinstance(data, dict):
                    delta = data.get("delta", {}) or data
                    message = delta.get("message", {}) if isinstance(delta, dict) else {}
                    content = ""
                    if isinstance(message, dict):
                        content = message.get("content", "")
                    elif isinstance(message, str):
                        content = message
                    if content:
                        has_content = True
                        break
                elif isinstance(data, str):
                    has_content = True
                    break

            assert has_content, "响应应包含内容"

        finally:
            # 清理插件
            await helper.cleanup_plugin(e2e_session, plugin_id, force=True)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invoke_tongyi_model_streaming(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        tongyi_api_key: str,
        tongyi_api_key_available: bool,
        plugin_provider,
    ) -> None:
        """
        测试流式调用 tongyi 模型并验证增量响应

        场景：流式调用模型
        - 以流式模式调用 tongyi 模型
        - 系统返回多个增量响应
        - 最后一个响应标记为完成
        """
        if not tongyi_api_key_available:
            pytest.skip("tongyi API Key 无效或服务不可用")

        plugin_id = "langgenius/tongyi"
        helper = PluginTestHelper(tenant_id=test_tenant_id)

        try:
            # 1. 安装并启动插件
            package_path: Path = plugin_package_path("tongyi")
            await helper.install_plugin_from_path(
                session=e2e_session,
                package_path=str(package_path),
                auto_start=True,
            )

            # 2. 等待插件状态为 ACTIVE
            await helper.wait_for_plugin_status(
                session=e2e_session,
                plugin_id=plugin_id,
                target_status=PluginStatus.ACTIVE,
                timeout=30.0,
            )

            # 3. 流式调用 tongyi 模型
            manager = await helper.get_manager(e2e_session)

            invoke_request = {
                "type": "model",
                "action": "invoke_llm",
                "user_id": f"{test_tenant_id}-user",
                "provider": "tongyi",
                "model_type": "llm",
                "model": "qwen-plus",
                "credentials": {
                    "dashscope_api_key": tongyi_api_key,
                },
                "prompt_messages": [
                    {
                        "role": "user",
                        "content": "请数数从1到5，每个数字占一行。",
                    }
                ],
                "model_parameters": {
                    "temperature": 0.1,
                    "max_tokens": 100,
                },
                "stream": True,
                "tools": None,
                "stop": None,
            }

            # 收集流式响应
            chunks = []
            async for chunk in manager.invoke_plugin_stream(
                e2e_session, plugin_id, invoke_request, timeout=60
            ):
                chunks.append(chunk)

            # 4. 验证流式响应
            assert len(chunks) >= 2, f"流式调用应返回多个响应块，实际收到 {len(chunks)} 个"

            # 验证增量内容
            accumulated_content = ""
            finish_reason = None

            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                data = chunk.get("data") or chunk
                if isinstance(data, dict):
                    delta = data.get("delta", {}) or data
                    if isinstance(delta, dict):
                        message = delta.get("message", {})
                        if isinstance(message, dict):
                            content = message.get("content", "")
                            if content:
                                accumulated_content += content
                        if delta.get("finish_reason"):
                            finish_reason = delta.get("finish_reason")
                    elif isinstance(delta, str):
                        accumulated_content += delta

            # 验证累积内容不为空
            assert len(accumulated_content) > 0, "流式响应应累积内容"

            # 验证最后一个响应标记完成
            assert finish_reason is not None, "最后一个响应应标记 finish_reason"

        finally:
            # 清理插件
            await helper.cleanup_plugin(e2e_session, plugin_id, force=True)


@pytest.mark.skipif(
    IS_WINDOWS,
    reason="Windows 上 gevent.os.tp_read 无法读取 asyncio 子进程 stdin 管道，"
    "导致插件调用超时。Linux 上正常。"
    "详见：gevent + ProactorEventLoop 管道兼容性",
)
class TestPluginInvokeGpustack:
    """gpustack 插件模型调用测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invoke_gpustack_model(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        gpustack_api_key: str,
        gpustack_endpoint: str,
        gpustack_api_key_available: bool,
        plugin_provider,
    ) -> None:
        """
        测试调用 gpustack 模型并验证响应

        场景：调用 gpustack 模型
        - 配置有效的 gpustack API Key 和 Endpoint
        - 调用模型生成接口
        - 系统成功调用 gpustack API
        - 返回有效的模型响应
        """
        # 使用 fixture 提供的 endpoint（优先环境变量，否则使用默认测试配置）
        if not gpustack_api_key_available:
            pytest.skip("GPUStack API Key 无效或服务不可用")

        endpoint_url = gpustack_endpoint

        # 检查模型名称环境变量（可选，有默认值）
        model_name = os.environ.get("E2E_GPUSTACK_MODEL", "qwen3.5-9b")

        plugin_id = "langgenius/gpustack"
        helper = PluginTestHelper(tenant_id=test_tenant_id)

        try:
            # 1. 安装并启动插件
            package_path: Path = plugin_package_path("gpustack")
            installed_plugin_id = await helper.install_plugin_from_path(
                session=e2e_session,
                package_path=str(package_path),
                auto_start=True,
            )
            assert installed_plugin_id == plugin_id, (
                f"插件 ID 应为 '{plugin_id}'，实际为 '{installed_plugin_id}'"
            )

            # 2. 等待插件状态为 ACTIVE
            await helper.wait_for_plugin_status(
                session=e2e_session,
                plugin_id=plugin_id,
                target_status=PluginStatus.ACTIVE,
                timeout=30.0,
            )

            # 3. 调用 gpustack 模型
            manager = await helper.get_manager(e2e_session)

            invoke_request = {
                "type": "model",
                "action": "invoke_llm",
                "user_id": f"{test_tenant_id}-user",
                "provider": "gpustack",
                "model_type": "llm",
                "model": model_name,
                "credentials": {
                    "api_key": gpustack_api_key,
                    "endpoint_url": endpoint_url,
                    "mode": "chat",
                    "context_size": "4096",
                },
                "prompt_messages": [
                    {
                        "role": "user",
                        "content": "你好，请用一句话介绍你自己。",
                    }
                ],
                "model_parameters": {
                    "temperature": 0.7,
                    "max_tokens": 100,
                },
                "stream": True,
                "tools": None,
                "stop": None,
            }

            # 调用并收集响应
            chunks = []
            async for chunk in manager.invoke_plugin_stream(
                e2e_session, plugin_id, invoke_request, timeout=60
            ):
                chunks.append(chunk)

            # 4. 验证响应
            assert len(chunks) > 0, "应收到至少一个响应块"

            # 验证响应内容（gpustack 可能在最后 chunk 聚合 usage 而不含 content）
            has_content = False
            has_tokens = False
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                data = chunk.get("data") or chunk
                if isinstance(data, dict):
                    delta = data.get("delta", {}) or data
                    if isinstance(delta, dict):
                        message = delta.get("message", {})
                        if isinstance(message, dict) and message.get("content"):
                            has_content = True
                            break
                    usage = delta.get("usage") if isinstance(delta, dict) else data.get("usage")
                    if isinstance(usage, dict) and usage.get("completion_tokens", 0) > 0:
                        has_tokens = True

            assert has_content or has_tokens, "响应应包含内容或 token 使用记录"

        finally:
            # 清理插件
            await helper.cleanup_plugin(e2e_session, plugin_id, force=True)


@pytest.mark.skipif(
    IS_WINDOWS,
    reason="Windows 上 gevent.os.tp_read 无法读取 asyncio 子进程 stdin 管道，"
    "导致插件调用超时。Linux 上正常。"
    "详见：gevent + ProactorEventLoop 管道兼容性",
)
class TestPluginInvokeError:
    """模型调用错误处理测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_invoke_with_invalid_api_key(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        plugin_provider,
    ) -> None:
        """
        测试使用无效 API Key 调用模型

        场景：调用失败时返回错误
        - 使用无效 API Key 调用模型
        - 系统返回认证失败错误
        - 错误包含详细错误信息
        """
        plugin_id = "langgenius/tongyi"
        helper = PluginTestHelper(tenant_id=test_tenant_id)

        try:
            # 1. 安装并启动插件
            package_path: Path = plugin_package_path("tongyi")
            await helper.install_plugin_from_path(
                session=e2e_session,
                package_path=str(package_path),
                auto_start=True,
            )

            # 2. 等待插件状态为 ACTIVE
            await helper.wait_for_plugin_status(
                session=e2e_session,
                plugin_id=plugin_id,
                target_status=PluginStatus.ACTIVE,
                timeout=30.0,
            )

            # 3. 使用无效 API Key 调用模型
            manager = await helper.get_manager(e2e_session)

            invoke_request = {
                "type": "model",
                "action": "invoke_llm",
                "user_id": f"{test_tenant_id}-user",
                "provider": "tongyi",
                "model_type": "llm",
                "model": "qwen-plus",
                "credentials": {
                    "dashscope_api_key": "invalid-api-key-for-testing-12345",
                },
                "prompt_messages": [
                    {
                        "role": "user",
                        "content": "你好",
                    }
                ],
                "model_parameters": {
                    "temperature": 0.7,
                    "max_tokens": 10,
                },
                "stream": True,
                "tools": None,
                "stop": None,
            }

            # 4. 验证调用失败并返回错误
            error_occurred = False
            error_message = ""

            try:
                chunks = []
                async for chunk in manager.invoke_plugin_stream(
                    e2e_session, plugin_id, invoke_request, timeout=60
                ):
                    chunks.append(chunk)
                    # 检查是否有错误响应
                    if chunk and "error" in chunk:
                        error_occurred = True
                        error_message = chunk.get("error", "")
            except Exception as e:
                error_occurred = True
                error_message = str(e)

            # 验证发生了错误
            assert error_occurred, "使用无效 API Key 应触发错误"

            # 验证错误信息包含认证相关内容
            error_lower = error_message.lower()
            is_auth_error = any(
                keyword in error_lower
                for keyword in ["auth", "key", "credential", "invalid", "unauthorized", "401", "403", "api"]
            )
            assert is_auth_error, (
                f"错误信息应包含认证相关内容，实际错误: {error_message}"
            )

        finally:
            # 清理插件
            await helper.cleanup_plugin(e2e_session, plugin_id, force=True)
