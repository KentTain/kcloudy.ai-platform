import binascii
import tempfile

from ai_plugin.sdk.entities.agent import AgentRuntime
from ai_plugin.sdk.entities.tool import ToolRuntime
from ai_plugin.sdk.interfaces.model.ai_model import AIModel
from ai_plugin.sdk.interfaces.model.large_language_model import LargeLanguageModel
from ai_plugin.sdk.interfaces.model.moderation_model import ModerationModel
from ai_plugin.sdk.interfaces.model.rerank_model import RerankModel
from ai_plugin.sdk.interfaces.model.speech2text_model import Speech2TextModel
from ai_plugin.sdk.interfaces.model.text_embedding_model import TextEmbeddingModel
from ai_plugin.sdk.interfaces.model.tts_model import TTSModel
from ai_plugin.sdk.interfaces.tool import ToolProvider
from ai_plugin.server.config.config import AlonPluginEnv
from ai_plugin.server.core.entities.plugin.request import (
    AgentInvokeRequest,
    ModelGetAIModelSchemas,
    ModelGetLLMNumTokens,
    ModelGetTextEmbeddingNumTokens,
    ModelGetTTSVoices,
    ModelInvokeLLMRequest,
    ModelInvokeModerationRequest,
    ModelInvokeRerankRequest,
    ModelInvokeSpeech2TextRequest,
    ModelInvokeTextEmbeddingRequest,
    ModelInvokeTTSRequest,
    ModelValidateModelCredentialsRequest,
    ModelValidateProviderCredentialsRequest,
    OAuthGetAuthorizationUrlRequest,
    OAuthGetCredentialsRequest,
    ToolGetRuntimeParametersRequest,
    ToolInvokeRequest,
    ToolValidateCredentialsRequest,
)
from ai_plugin.server.core.plugin_registration import PluginRegistration
from ai_plugin.server.core.runtime import Session
from ai_plugin.server.core.utils.http_parser import parse_raw_request
from ai_plugin.server.protocol.oauth import OAuthProviderProtocol


class PluginExecutor:
    """插件执行器

    负责执行各种插件操作，包括工具调用、模型调用、代理策略调用等。
    """

    def __init__(self, config: AlonPluginEnv, registration: PluginRegistration) -> None:
        """初始化插件执行器

        Args:
            config: 插件环境配置
            registration: 插件注册管理器
        """
        self.config = config
        self.registration = registration

    def validate_tool_provider_credentials(
        self, session: Session, data: ToolValidateCredentialsRequest
    ):
        """验证工具提供者凭证

        Args:
            session: 会话实例
            data: 工具凭证验证请求数据

        Returns:
            验证结果字典

        Raises:
            ValueError: 当提供者未找到时抛出
        """
        provider_instance = self.registration.get_tool_provider_cls(data.provider)
        if provider_instance is None:
            raise ValueError(f"提供者 `{data.provider}` 未找到")

        provider_instance = provider_instance()
        provider_instance.validate_credentials(data.credentials)

        return {"result": True}

    def invoke_tool(self, session: Session, request: ToolInvokeRequest):
        """调用工具

        Args:
            session: 会话实例
            request: 工具调用请求

        Yields:
            工具执行结果

        Raises:
            ValueError: 当提供者或工具未找到时抛出
        """
        provider_cls = self.registration.get_tool_provider_cls(request.provider)
        if provider_cls is None:
            raise ValueError(f"提供者 `{request.provider}` 未找到")

        tool_cls = self.registration.get_tool_cls(request.provider, request.tool)
        if tool_cls is None:
            raise ValueError(
                f"工具 `{request.tool}` 在提供者 `{request.provider}` 中未找到"
            )

        # 实例化工具
        tool = tool_cls(
            runtime=ToolRuntime(
                credentials=request.credentials,
                user_id=request.user_id,
                session_id=session.session_id,
            ),
            session=session,
        )

        # 调用工具
        yield from tool.invoke(request.tool_parameters)

    def invoke_agent_strategy(self, session: Session, request: AgentInvokeRequest):
        """调用代理策略

        Args:
            session: 会话实例
            request: 代理调用请求

        Yields:
            代理执行结果

        Raises:
            ValueError: 当代理策略未找到时抛出
        """
        agent_cls = self.registration.get_agent_strategy_cls(
            request.agent_strategy_provider, request.agent_strategy
        )
        if agent_cls is None:
            raise ValueError(
                f"代理 `{request.agent_strategy}` 在提供者 `{request.agent_strategy_provider}` 中未找到"
            )

        agent = agent_cls(
            runtime=AgentRuntime(
                user_id=request.user_id,
            ),
            session=session,
        )
        yield from agent.invoke(request.agent_strategy_params)

    def get_tool_runtime_parameters(
        self, session: Session, data: ToolGetRuntimeParametersRequest
    ):
        """获取工具运行时参数

        Args:
            session: 会话实例
            data: 工具运行时参数请求数据

        Returns:
            包含参数的字典

        Raises:
            ValueError: 当工具未找到或不支持运行时参数时抛出
        """
        tool_cls = self.registration.get_tool_cls(data.provider, data.tool)
        if tool_cls is None:
            raise ValueError(f"工具 `{data.tool}` 在提供者 `{data.provider}` 中未找到")

        if not tool_cls._is_get_runtime_parameters_overridden():
            raise ValueError(f"工具 `{data.tool}` 未实现运行时参数")

        tool_instance = tool_cls(
            runtime=ToolRuntime(
                credentials=data.credentials,
                user_id=data.user_id,
                session_id=session.session_id,
            ),
            session=session,
        )

        return {
            "parameters": tool_instance.get_runtime_parameters(),
        }

    def validate_model_provider_credentials(
        self, session: Session, data: ModelValidateProviderCredentialsRequest
    ):
        """验证模型提供者凭证

        Args:
            session: 会话实例
            data: 模型提供者凭证验证请求数据

        Returns:
            验证结果字典

        Raises:
            ValueError: 当提供者未找到时抛出
        """
        provider_instance = self.registration.get_model_provider_instance(data.provider)
        if provider_instance is None:
            raise ValueError(f"提供者 `{data.provider}` 未找到")

        provider_instance.validate_provider_credentials(data.credentials)

        return {"result": True, "credentials": data.credentials}

    def validate_model_credentials(
        self, session: Session, data: ModelValidateModelCredentialsRequest
    ):
        """验证模型凭证

        Args:
            session: 会话实例
            data: 模型凭证验证请求数据

        Returns:
            验证结果字典

        Raises:
            ValueError: 当提供者或模型未找到时抛出
        """
        provider_instance = self.registration.get_model_provider_instance(data.provider)
        if provider_instance is None:
            raise ValueError(f"提供者 `{data.provider}` 未找到")

        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if model_instance is None:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

        model_instance.validate_credentials(data.model, data.credentials)

        return {"result": True, "credentials": data.credentials}

    def invoke_llm(self, session: Session, data: ModelInvokeLLMRequest):
        """调用大语言模型

        Args:
            session: 会话实例
            data: 大语言模型调用请求数据

        Returns:
            模型调用结果

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, LargeLanguageModel):
            return model_instance.invoke(
                data.model,
                data.credentials,
                data.prompt_messages,
                data.model_parameters,
                data.tools,
                data.stop,
                data.stream,
                data.user_id,
            )
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def get_llm_num_tokens(self, session: Session, data: ModelGetLLMNumTokens):
        """获取大语言模型token数量

        Args:
            session: 会话实例
            data: 获取LLM token数量请求数据

        Returns:
            包含token数量的字典

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )

        if isinstance(model_instance, LargeLanguageModel):
            return {
                "num_tokens": model_instance.get_num_tokens(
                    data.model,
                    data.credentials,
                    data.prompt_messages,
                    data.tools,
                ),
            }
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def invoke_text_embedding(
        self, session: Session, data: ModelInvokeTextEmbeddingRequest
    ):
        """调用文本嵌入模型

        Args:
            session: 会话实例
            data: 文本嵌入模型调用请求数据

        Returns:
            文本嵌入结果

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, TextEmbeddingModel):
            return model_instance.invoke(
                data.model,
                data.credentials,
                data.texts,
                data.user_id,
            )
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def get_text_embedding_num_tokens(
        self, session: Session, data: ModelGetTextEmbeddingNumTokens
    ):
        """获取文本嵌入模型token数量

        Args:
            session: 会话实例
            data: 获取文本嵌入token数量请求数据

        Returns:
            包含token数量的字典

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, TextEmbeddingModel):
            return {
                "num_tokens": model_instance.get_num_tokens(
                    data.model,
                    data.credentials,
                    data.texts,
                ),
            }
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def invoke_rerank(self, session: Session, data: ModelInvokeRerankRequest):
        """调用重排序模型

        Args:
            session: 会话实例
            data: 重排序模型调用请求数据

        Returns:
            重排序结果

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, RerankModel):
            return model_instance.invoke(
                data.model,
                data.credentials,
                data.query,
                data.docs,
                data.score_threshold,
                data.top_n,
                data.user_id,
            )
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def invoke_tts(self, session: Session, data: ModelInvokeTTSRequest):
        """调用文本转语音模型

        Args:
            session: 会话实例
            data: TTS模型调用请求数据

        Yields:
            TTS生成的音频数据（十六进制编码）

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, TTSModel):
            b = model_instance.invoke(
                data.model,
                data.tenant_id,
                data.credentials,
                data.content_text,
                data.voice,
                data.user_id,
            )
            # 如果返回的是字节数据，直接编码并返回
            if isinstance(b, bytes | bytearray | memoryview):
                yield {"result": binascii.hexlify(b).decode()}
                return

            # 如果返回的是生成器，逐块编码返回
            for chunk in b:
                yield {"result": binascii.hexlify(chunk).decode()}
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def get_tts_model_voices(self, session: Session, data: ModelGetTTSVoices):
        """获取TTS模型可用语音

        Args:
            session: 会话实例
            data: 获取TTS语音请求数据

        Returns:
            包含可用语音列表的字典

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, TTSModel):
            return {
                "voices": model_instance.get_tts_model_voices(
                    data.model, data.credentials, data.language
                )
            }
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def invoke_speech_to_text(
        self, session: Session, data: ModelInvokeSpeech2TextRequest
    ):
        """调用语音转文本模型

        Args:
            session: 会话实例
            data: 语音转文本模型调用请求数据

        Returns:
            语音识别结果

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )

        # 创建临时文件存储音频数据
        with tempfile.NamedTemporaryFile(suffix=".mp3", mode="wb", delete=True) as temp:
            # 解码十六进制音频数据并写入临时文件
            temp.write(binascii.unhexlify(data.file))
            temp.flush()

            # 打开临时文件进行读取
            with open(temp.name, "rb") as f:
                if isinstance(model_instance, Speech2TextModel):
                    return {
                        "result": model_instance.invoke(
                            data.model,
                            data.credentials,
                            f,
                            data.user_id,
                        ),
                    }
                else:
                    raise ValueError(
                        f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
                    )

    def get_ai_model_schemas(self, session: Session, data: ModelGetAIModelSchemas):
        """获取AI模型模式

        Args:
            session: 会话实例
            data: 获取AI模型模式请求数据

        Returns:
            包含模型模式的字典

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, AIModel):
            return {
                "model_schema": model_instance.get_model_schema(
                    data.model, data.credentials
                )
            }
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def invoke_moderation(self, session: Session, data: ModelInvokeModerationRequest):
        """调用内容审核模型

        Args:
            session: 会话实例
            data: 内容审核模型调用请求数据

        Returns:
            内容审核结果

        Raises:
            ValueError: 当模型类型不匹配时抛出
        """
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )

        if isinstance(model_instance, ModerationModel):
            return {
                "result": model_instance.invoke(
                    data.model,
                    data.credentials,
                    data.text,
                    data.user_id,
                ),
            }
        else:
            raise ValueError(
                f"模型 `{data.model_type}` 在提供者 `{data.provider}` 中未找到"
            )

    def _get_oauth_provider_instance(self, provider: str) -> OAuthProviderProtocol:
        """获取OAuth提供者实例

        Args:
            provider: 提供者名称

        Returns:
            OAuth提供者协议实例

        Raises:
            ValueError: 当提供者不支持OAuth时抛出
        """
        provider_cls = self.registration.get_supported_oauth_provider_cls(provider)
        if provider_cls is None:
            raise ValueError(f"提供者 `{provider}` 不支持OAuth")

        if provider_cls == ToolProvider:
            return provider_cls()

        raise ValueError(f"提供者 `{provider}` 不支持OAuth")

    def get_oauth_authorization_url(
        self, session: Session, data: OAuthGetAuthorizationUrlRequest
    ):
        """获取OAuth授权URL

        Args:
            session: 会话实例
            data: OAuth授权URL获取请求数据

        Returns:
            授权URL信息
        """
        provider_instance = self._get_oauth_provider_instance(data.provider)

        return {
            "authorization_url": provider_instance.oauth_get_authorization_url(
                data.system_credentials
            ),
        }

    def get_oauth_credentials(self, session: Session, data: OAuthGetCredentialsRequest):
        """获取OAuth凭证

        Args:
            session: 会话实例
            data: OAuth凭证获取请求数据

        Returns:
            OAuth凭证信息
        """
        provider_instance = self._get_oauth_provider_instance(data.provider)
        # 解码十六进制HTTP请求数据
        bytes_data = binascii.unhexlify(data.raw_http_request)
        request = parse_raw_request(bytes_data)

        return {
            "credentials": provider_instance.oauth_get_credentials(
                data.system_credentials, request
            ),
        }
