"""
内存模型客户端实现
直接调用插件引擎的内部API，适用于插件引擎和主服务在同一进程的场景
"""

import time
from collections.abc import AsyncGenerator

from loguru import logger

from alon.components.model.entities.plugin_entities import PluginModelProviderEntity
from ai.components.plugin.client.base import BasePluginClient
from ai.components.plugin.client.stream_printer import StreamPrinter
from ai_plugin.sdk.entities.model import AIModelEntity, ModelType
from ai_plugin.sdk.entities.model.llm import LLMResultChunk
from ai_plugin.sdk.entities.model.message import PromptMessage, PromptMessageTool
from ai_plugin.sdk.entities.model.rerank import RerankResult
from ai_plugin.sdk.entities.model.text_embedding import TextEmbeddingResult
from ai_plugin.server.core.entities.plugin.request import (
    ModelGetAIModelSchemas,
    ModelGetLLMNumTokens,
    ModelGetTextEmbeddingNumTokens,
    ModelInvokeLLMRequest,
    ModelInvokeRerankRequest,
    ModelInvokeTextEmbeddingRequest,
    ModelValidateModelCredentialsRequest,
    ModelValidateProviderCredentialsRequest,
)


# @remotable()
class ModelClient(BasePluginClient):
    """内存模型客户端实现类"""

    def __init__(self):
        """初始化模型客户端"""
        super().__init__()
        self.stream_printer = StreamPrinter()

    async def fetch_model_providers(
        self, tenant_id: str
    ) -> list[PluginModelProviderEntity]:
        """获取租户的模型提供者列表"""

        plugin_manager = await self._get_plugin_manager(tenant_id)

        # 直接调用插件管理器获取模型提供者
        providers = []
        from datetime import datetime

        now = datetime.now()

        for plugin_name, plugin_info in plugin_manager.plugins.items():
            try:
                # 创建完整的模型提供者数据

                # 创建ProviderEntity
                for config in plugin_info.config.models_configuration or []:
                    # 创建完整的PluginModelProviderEntity
                    providers.append(
                        PluginModelProviderEntity(
                            id=f"provider-{plugin_name}",
                            created_at=now,
                            updated_at=now,
                            provider=config.provider,
                            tenant_id=tenant_id,
                            plugin_unique_identifier=f"{plugin_name}@{plugin_info.config.configuration.version}",
                            plugin_id=plugin_name,
                            declaration=config.model_copy(),  # 使用 model_copy() 避免副作用
                        ),
                    )

            except Exception as e:
                logger.error(f"获取模型提供者失败: {plugin_name}, {e}")

        return providers

    async def get_model_schema(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model_type: ModelType,
        model: str,
        credentials: dict,
    ) -> AIModelEntity | None:
        """获取模型配置结构"""

        start_time = time.time()

        plugin_manager = await self._get_plugin_manager(tenant_id)

        try:
            # 调用插件管理器获取模型结构
            parameters = {
                "user_id": user_id,
                "provider": provider,
                "model_type": model_type,
                "model": model,
                "credentials": credentials,
            }

            # 调用插件管理器获取模型结构
            parameters = ModelGetAIModelSchemas(
                user_id=user_id,
                provider=provider,
                model_type=model_type,
                model=model,
                credentials=credentials,
            )

            result = plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            )
            return_result: AIModelEntity | None = None

            async for chunk in result:
                logger.debug("get_model_schema---->")
                chunk = self._extract_result_data(chunk)
                if "model_schema" in chunk:
                    return_result = AIModelEntity(**chunk.get("model_schema", None))

            logger.info(
                f"get_model_schema available 耗时: {time.time() - start_time} 秒"
            )

            return return_result
        except Exception as e:
            logger.error(f"获取模型配置结构失败: {e}")
            return None

    async def validate_provider_credentials(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        credentials: dict,
    ) -> bool:
        """验证提供者凭证"""
        try:
            plugin_manager = await self._get_plugin_manager(tenant_id)

            parameters = ModelValidateProviderCredentialsRequest(
                user_id=user_id,
                provider=provider,
                credentials=credentials,
            )

            return_result = False

            async for chunk in plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            ):
                logger.debug("validate_provider_credentials---->")
                chunk = self._extract_result_data(chunk)
                if "result" in chunk:
                    return_result = chunk.get("result", False)

            return return_result

        except Exception as e:
            logger.error(f"验证提供者凭证失败: {e}")
            return False

    async def validate_model_credentials(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model_type: ModelType,
        model: str,
        credentials: dict,
    ) -> bool:
        """验证模型凭证"""

        plugin_manager = await self._get_plugin_manager(tenant_id)

        try:
            parameters = ModelValidateModelCredentialsRequest(
                user_id=user_id,
                provider=provider,
                model_type=model_type,
                model=model,
                credentials=credentials,
            )
            return_result = False

            async for chunk in plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            ):
                logger.debug("validate_model_credentials---->")
                chunk = self._extract_result_data(chunk)
                if "result" in chunk:
                    return_result = chunk.get("result", False)

            return return_result
        except Exception as e:
            logger.error(f"验证模型凭证失败: {e}")
            return False

    async def invoke_llm(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict | None = None,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
    ) -> AsyncGenerator[LLMResultChunk, None]:
        """调用大语言模型"""

        plugin_manager = await self._get_plugin_manager(tenant_id)
        session_id = None
        enable_batch_print: bool = True

        try:
            # 创建打印会话（如果启用批量打印）
            if enable_batch_print:
                session_id = self.stream_printer.create_session(
                    "llm",
                    model=model,
                    provider=provider,
                    user_id=user_id,
                    plugin_id=plugin_id,
                )
                # 收集输入消息
                self.stream_printer.collect_prompt_messages(
                    session_id, prompt_messages, tools=tools
                )

            parameters = ModelInvokeLLMRequest(
                user_id=user_id,
                provider=provider,
                model_type=ModelType.LLM,
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters or {},
                tools=tools,
                stop=stop,
                stream=True,
            )

            result = plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            )
            async for chunk in result:
                chunk = self._extract_result_data(chunk)
                result_chunk = LLMResultChunk(**chunk)

                # 收集输出或直接打印
                if enable_batch_print and session_id:
                    self.stream_printer.collect_llm_stream_content(
                        session_id, result_chunk
                    )

                yield result_chunk

            # 完成会话并打印结果
            if enable_batch_print and session_id:
                self.stream_printer.complete_session(session_id)

        except Exception as e:
            # 如果出现异常，也要完成会话
            if enable_batch_print and session_id:
                self.stream_printer.complete_session(session_id)
            logger.error(f"LLM调用失败: {e}")
            raise e

    async def get_llm_num_tokens(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
    ) -> int:
        """获取LLM Token数量"""

        plugin_manager = await self._get_plugin_manager(tenant_id)

        try:
            parameters = ModelGetLLMNumTokens(
                user_id=user_id,
                provider=provider,
                model_type=ModelType.LLM,
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                tools=tools,
            )

            return_result = 0

            result = plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            )
            async for chunk in result:
                logger.debug("get_llm_num_tokens---->")
                chunk = self._extract_result_data(chunk)
                if "num_tokens" in chunk:
                    return_result = chunk.get("num_tokens", 0)

            return return_result
        except Exception as e:
            logger.error(f"获取LLM Token数量失败: {e}")
            return 0

    async def invoke_text_embedding(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model: str,
        credentials: dict,
        texts: list[str],
    ) -> TextEmbeddingResult:
        """调用文本嵌入模型"""
        try:
            plugin_manager = await self._get_plugin_manager(tenant_id)

            parameters = ModelInvokeTextEmbeddingRequest(
                user_id=user_id,
                provider=provider,
                model_type=ModelType.TEXT_EMBEDDING,
                model=model,
                credentials=credentials,
                texts=texts,
            )

            result = plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            )
            return_result: TextEmbeddingResult | None = None
            async for chunk in result:
                logger.debug("invoke_text_embedding---->")
                chunk = self._extract_result_data(chunk)

                if "embeddings" in chunk:
                    return_result = TextEmbeddingResult(**chunk)

            if return_result is None:
                raise ValueError("获取文本嵌入Token数量失败")

            return return_result

        except Exception as e:
            logger.error(f"文本嵌入调用失败: {e}")
            raise ValueError(str(e))

    async def get_text_embedding_num_tokens(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model: str,
        credentials: dict,
        texts: list[str],
    ) -> list[int]:
        """获取文本嵌入Token数量"""
        try:
            plugin_manager = await self._get_plugin_manager(tenant_id)

            parameters = ModelGetTextEmbeddingNumTokens(
                user_id=user_id,
                provider=provider,
                model_type=ModelType.TEXT_EMBEDDING,
                model=model,
                credentials=credentials,
                texts=texts,
            )

            result = plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            )
            return_result: list[int] = []
            async for chunk in result:
                logger.debug("get_text_embedding_num_tokens---->")
                chunk = self._extract_result_data(chunk)
                if "num_tokens" in chunk:
                    return_result = chunk.get("num_tokens", [])

            return return_result

        except Exception as e:
            logger.error(f"获取文本嵌入Token数量失败: {e}")
            return []

    async def invoke_rerank(
        self,
        tenant_id: str,
        user_id: str,
        plugin_id: str,
        provider: str,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: float | None = None,
        top_n: int | None = None,
    ) -> RerankResult:
        """调用重排序模型"""
        try:
            plugin_manager = await self._get_plugin_manager(tenant_id)

            parameters = ModelInvokeRerankRequest(
                user_id=user_id,
                provider=provider,
                model_type=ModelType.RERANK,
                model=model,
                credentials=credentials,
                query=query,
                docs=docs,
                score_threshold=score_threshold,
                top_n=top_n,
            )

            result = plugin_manager.invoke_plugin_stream(
                plugin_id, parameters.model_dump()
            )
            return_result: RerankResult | None = None
            async for chunk in result:
                logger.debug("invoke_rerank---->")
                chunk = self._extract_result_data(chunk)
                if "docs" in chunk:
                    return_result = RerankResult(**chunk)

            if return_result is None:
                raise ValueError("重排序调用失败")

            return return_result
        except Exception as e:
            logger.error(f"重排序调用失败: {e}")
            raise ValueError(str(e))

    # async def invoke_tts(
    #     self,
    #     tenant_id: str,
    #     user_id: str,
    #     plugin_id: str,
    #     provider: str,
    #     model: str,
    #     credentials: dict,
    #     content_text: str,
    #     voice: str,
    # ) -> AsyncGenerator[bytes, None]:
    #     """调用文本转语音模型"""
    #     try:
    #         plugin_manager = await self.__get_plugin_manager(tenant_id)

    #         parameters = ModelInvokeTTSRequest(
    #             user_id=user_id,
    #             provider=provider,
    #             model_type=ModelType.TTS,
    #             model=model,
    #             credentials=credentials,
    #             content_text=content_text,
    #             voice=voice,
    #             tenant_id=tenant_id,
    #         )

    #         result = plugin_manager.invoke_plugin_stream(plugin_id, parameters.model_dump())
    #         async for chunk in result:
    #             logger.debug("invoke_tts---->")
    #             return chunk

    #         # 处理音频数据流
    #         if actual_result.get("audio_chunks"):
    #             for chunk in actual_result["audio_chunks"]:
    #                 if isinstance(chunk, str):
    #                     yield binascii.unhexlify(chunk)
    #                 else:
    #                     yield chunk
    #         elif actual_result.get("audio_data"):
    #             # 如果返回的是完整的音频数据
    #             audio_data = actual_result["audio_data"]
    #             if isinstance(audio_data, str):
    #                 yield binascii.unhexlify(audio_data)
    #             else:
    #                 yield audio_data
    #     except Exception as e:
    #         logger.error(f"TTS调用失败: {e}")
    #         raise ValueError(str(e))

    # async def get_tts_model_voices(
    #     self,
    #     tenant_id: str,
    #     user_id: str,
    #     plugin_id: str,
    #     provider: str,
    #     model: str,
    #     credentials: dict,
    #     language: Optional[str] = None,
    # ) -> list[dict]:
    #     """获取TTS模型声音列表"""
    #     try:
    #         parameters = {
    #             "user_id": user_id,
    #             "provider": provider,
    #             "model_type": ModelType.TTS.value,
    #             "model": model,
    #             "credentials": credentials,
    #             "language": language,
    #         }

    #         result = await self.plugin_manager.invoke_plugin(plugin_id, "get_tts_model_voices", parameters)
    #         actual_result = self._extract_result_data(result)

    #         voices = []
    #         if actual_result.get("voices"):
    #             for voice in actual_result["voices"]:
    #                 if isinstance(voice, dict):
    #                     voices.append({"name": voice.get("name"), "value": voice.get("value")})
    #                 else:
    #                     voices.append(
    #                         {
    #                             "name": voice.name if hasattr(voice, "name") else str(voice),
    #                             "value": voice.value if hasattr(voice, "value") else str(voice),
    #                         }
    #                     )

    #         return voices
    #     except Exception as e:
    #         logger.error(f"获取TTS声音列表失败: {e}")
    #         return []

    # async def invoke_speech_to_text(
    #     self,
    #     tenant_id: str,
    #     user_id: str,
    #     plugin_id: str,
    #     provider: str,
    #     model: str,
    #     credentials: dict,
    #     file: IO[bytes],
    # ) -> str:
    #     """调用语音转文本模型"""
    #     try:
    #         parameters = {
    #             "user_id": user_id,
    #             "provider": provider,
    #             "model_type": ModelType.SPEECH2TEXT.value,
    #             "model": model,
    #             "credentials": credentials,
    #             "file": binascii.hexlify(file.read()).decode(),
    #         }

    #         result = await self.plugin_manager.invoke_plugin(plugin_id, "invoke_speech_to_text", parameters)
    #         actual_result = self._extract_result_data(result)
    #         return actual_result.get("result", "")
    #     except Exception as e:
    #         logger.error(f"语音转文本调用失败: {e}")
    #         raise ValueError(str(e))

    # async def invoke_moderation(
    #     self,
    #     tenant_id: str,
    #     user_id: str,
    #     plugin_id: str,
    #     provider: str,
    #     model: str,
    #     credentials: dict,
    #     text: str,
    # ) -> bool:
    #     """调用内容审核模型"""
    #     try:
    #         parameters = {
    #             "user_id": user_id,
    #             "provider": provider,
    #             "model_type": ModelType.MODERATION.value,
    #             "model": model,
    #             "credentials": credentials,
    #             "text": text,
    #         }

    #         result = await self.plugin_manager.invoke_plugin(plugin_id, "invoke_moderation", parameters)
    #         actual_result = self._extract_result_data(result)
    #         return actual_result.get("result", False)
    #     except Exception as e:
    #         logger.error(f"内容审核调用失败: {e}")
    #         raise ValueError(str(e))
