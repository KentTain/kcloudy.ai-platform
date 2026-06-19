from typing import Any
from collections.abc import AsyncGenerator

from loguru import logger

from ai.components.plugin.client.base import BasePluginClient
from ai.components.plugin.client.plugin.entities.plugin import GenericProviderID
from ai.components.plugin.client.plugin.entities.plugin_daemon import (
    PluginToolProviderEntity,
    ToolProviderEntityWithPlugin,
)
from ai.components.plugin.client.stream_printer import StreamPrinter
from ai.components.plugin.engine.models.plugin import PluginInfo
from ai_plugin.sdk.entities.tool import (
    ToolInvokeMessage,
    ToolParameter,
    ToolProviderConfiguration,
    ToolProviderType,
)
from ai_plugin.sdk.interfaces.agent import AgentToolIdentity, ToolEntity
from ai_plugin.server.core.entities.plugin.request import (
    ToolGetRuntimeParametersRequest,
    ToolInvokeRequest,
    ToolValidateCredentialsRequest,
)


# @remotable()
class ToolClient(BasePluginClient):
    """
    工具管理器
    """

    def __init__(self):
        """初始化工具客户端"""
        super().__init__()
        self.stream_printer = StreamPrinter()

    async def fetch_tool_providers(
        self, tenant_id: str
    ) -> list[PluginToolProviderEntity]:
        """获取租户的工具提供者列表"""

        plugin_manager = await self._get_plugin_manager(tenant_id)

        providers = []

        for plugin_name, plugin_info in plugin_manager.plugins.items():
            try:
                # 创建完整的工具提供者数据

                # 创建ToolProviderEntity
                for config in plugin_info.config.tools_configuration or []:
                    provider_entity = config.model_copy()

                    # 创建完整的PluginToolProviderEntity
                    providers.append(
                        self._create_plugin_tool_provider_entity(
                            plugin_name, plugin_info, provider_entity
                        ),
                    )

            except Exception as e:
                logger.error(f"获取工具提供者失败: {plugin_name}, {e}")

        return providers

    def _create_plugin_tool_provider_entity(
        self,
        plugin_name: str,
        plugin_info: PluginInfo,
        provider_entity: ToolProviderConfiguration,
    ) -> PluginToolProviderEntity:
        """创建插件工具提供者实体"""
        return PluginToolProviderEntity(
            provider=provider_entity.identity.name,
            plugin_unique_identifier=f"{plugin_name}@{plugin_info.config.configuration.version}",
            plugin_id=plugin_name,
            declaration=ToolProviderEntityWithPlugin(
                identity=provider_entity.identity,
                credentials_schema=provider_entity.credentials_schema,
                plugin_id=plugin_name,
                tools=[
                    ToolEntity(
                        identity=AgentToolIdentity(
                            name=tool.identity.name,
                            author=tool.identity.author,
                            label=tool.identity.label,
                            provider=provider_entity.identity.name,
                        ),
                        parameters=tool.parameters,
                        description=tool.description,
                        output_schema=tool.output_schema,
                        has_runtime_parameters=tool.has_runtime_parameters,
                        runtime_parameters={},
                        provider_type=ToolProviderType.BUILT_IN,
                    )
                    for tool in provider_entity.tools
                ],
            ),
        )

    async def fetch_tool_provider(
        self, tenant_id: str, provider: str
    ) -> PluginToolProviderEntity | None:
        """获取租户的工具提供者"""

        tool_provider_id = GenericProviderID(provider)
        plugin_id = f"{tool_provider_id.organization}/{tool_provider_id.plugin_name}"

        plugin_manager = await self._get_plugin_manager(tenant_id)

        for plugin_name, plugin_info in plugin_manager.plugins.items():
            try:
                # 创建完整的工具提供者数据

                if plugin_id != plugin_name:
                    continue

                # 创建ToolProviderEntity
                for config in plugin_info.config.tools_configuration or []:
                    provider_entity = config.model_copy()

                    # 创建完整的PluginToolProviderEntity
                    return self._create_plugin_tool_provider_entity(
                        plugin_name, plugin_info, provider_entity
                    )

            except Exception as e:
                logger.error(f"获取工具提供者失败: {plugin_name}, {e}")

        return None

    async def invoke(
        self,
        tenant_id: str,
        user_id: str,
        tool_provider: str,
        tool_name: str,
        credentials: dict[str, Any],
        tool_parameters: dict[str, Any],
        conversation_id: str | None = None,
        app_id: str | None = None,
        message_id: str | None = None,
    ) -> AsyncGenerator[ToolInvokeMessage, None]:
        """
        调用工具
        """

        tool_provider_id = GenericProviderID(tool_provider)
        plugin_id = f"{tool_provider_id.organization}/{tool_provider_id.plugin_name}"

        session_id = None
        enable_batch_print: bool = True

        # 创建打印会话（如果启用批量打印）
        if enable_batch_print:
            session_id = self.stream_printer.create_session(
                "tool",
                tool_provider=tool_provider,
                tool_name=tool_name,
                user_id=user_id,
                plugin_id=plugin_id,
            )
            # 收集工具调用参数
            self.stream_printer.collect_tool_invoke_params(
                session_id=session_id,
                tool_provider=tool_provider,
                tool_name=tool_name,
                tool_parameters=tool_parameters,
                credentials=credentials,
                user_id=user_id,
            )

        tool_invoke_request = ToolInvokeRequest(
            user_id=user_id,
            provider=tool_provider_id.provider_name,
            tool=tool_name,
            credentials=credentials,
            tool_parameters=tool_parameters,
        )

        class FileChunk:
            """
            只用于内部处理。
            """

            bytes_written: int
            total_length: int
            data: bytearray

            def __init__(self, total_length: int):
                self.bytes_written = 0
                self.total_length = total_length
                self.data = bytearray(total_length)

        files: dict[str, FileChunk] = {}

        plugin_manager = await self._get_plugin_manager(tenant_id)

        try:
            result = plugin_manager.invoke_plugin_stream(
                plugin_id, tool_invoke_request.model_dump()
            )
            async for chunk in result:
                chunk = self._extract_result_data(chunk)
                resp = ToolInvokeMessage(**chunk)

                # 收集工具响应或直接打印
                if enable_batch_print and session_id:
                    self.stream_printer.collect_tool_invoke_message(session_id, resp)

                if resp.type == ToolInvokeMessage.MessageType.BLOB_CHUNK:
                    assert isinstance(resp.message, ToolInvokeMessage.BlobChunkMessage)
                    # 获取blob chunk信息
                    chunk_id = resp.message.id
                    total_length = resp.message.total_length
                    blob_data = resp.message.blob
                    is_end = resp.message.end

                    # 初始化文件缓冲区
                    if chunk_id not in files:
                        files[chunk_id] = FileChunk(total_length)

                    # 如果这是最后一个chunk，则yield一个完整的blob消息
                    if is_end:
                        yield ToolInvokeMessage(
                            type=ToolInvokeMessage.MessageType.BLOB,
                            message=ToolInvokeMessage.BlobMessage(
                                blob=files[chunk_id].data
                            ),
                            meta=resp.meta,
                        )
                    else:
                        # 检查文件是否太大（30MB限制）
                        if (
                            files[chunk_id].bytes_written + len(blob_data)
                            > 30 * 1024 * 1024
                        ):
                            # 删除文件如果它太大
                            del files[chunk_id]
                            # 跳过yield这个消息
                            raise ValueError("文件太大，超过30MB限制")

                        # 检查单个chunk是否太大（8KB限制）
                        if len(blob_data) > 8192:
                            # 跳过yield这个消息
                            raise ValueError("单个chunk太大，超过8KB限制")

                        # 将blob数据追加到缓冲区
                        files[chunk_id].data[
                            files[chunk_id].bytes_written : files[
                                chunk_id
                            ].bytes_written
                            + len(blob_data)
                        ] = blob_data
                        files[chunk_id].bytes_written += len(blob_data)
                else:
                    yield resp

            # 完成会话并打印结果
            if enable_batch_print and session_id:
                self.stream_printer.complete_session(session_id)

        except Exception as e:
            # 如果出现异常，也要完成会话
            if enable_batch_print and session_id:
                self.stream_printer.complete_session(session_id)
            raise e

    async def validate_provider_credentials(
        self,
        tenant_id: str,
        user_id: str,
        provider: str,
        credentials: dict[str, Any],
    ) -> bool:
        """
        验证提供者的凭证
        """

        plugin_manager = await self._get_plugin_manager(tenant_id)

        tool_provider_id = GenericProviderID(provider)

        tool_validate_credentials_request = ToolValidateCredentialsRequest(
            user_id=user_id,
            provider=tool_provider_id.provider_name,
            credentials=credentials,
        )

        plugin_id = f"{tool_provider_id.organization}/{tool_provider_id.plugin_name}"

        try:
            result = plugin_manager.invoke_plugin_stream(
                plugin_id, tool_validate_credentials_request.model_dump()
            )
            return_result = False

            async for chunk in result:
                logger.debug("validate_provider_credentials---->")
                chunk = self._extract_result_data(chunk)
                if "result" in chunk:
                    return_result = chunk.get("result", False)

            return return_result

        except Exception as e:
            logger.error(f"验证提供者凭证失败: {e}")
            return False

    async def get_runtime_parameters(
        self,
        tenant_id: str,
        user_id: str,
        provider: str,
        credentials: dict[str, Any],
        tool: str,
        conversation_id: str | None = None,
        app_id: str | None = None,
        message_id: str | None = None,
    ) -> list[ToolParameter]:
        """
        获取工具的运行时参数
        """

        plugin_manager = await self._get_plugin_manager(tenant_id)

        tool_provider_id = GenericProviderID(provider)

        tool_get_runtime_parameters_request = ToolGetRuntimeParametersRequest(
            user_id=user_id,
            provider=tool_provider_id.provider_name,
            tool=tool,
            credentials=credentials,
        )

        plugin_id = f"{tool_provider_id.organization}/{tool_provider_id.plugin_name}"

        result = plugin_manager.invoke_plugin_stream(
            plugin_id, tool_get_runtime_parameters_request.model_dump()
        )

        return_result = []

        async for chunk in result:
            logger.debug("get_runtime_parameters---->")

            chunk = self._extract_result_data(chunk)
            if "parameters" in chunk:
                return_result = chunk.get("parameters", [])

        return return_result
