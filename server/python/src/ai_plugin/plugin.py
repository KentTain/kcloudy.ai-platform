import base64
import logging
import uuid
from collections.abc import Generator
from typing import Any

from pydantic import RootModel
from yarl import URL

from ai_plugin.sdk.entities.tool import ToolInvokeMessage
from ai_plugin.server.config.config import AlonPluginEnv, InstallMethod
from ai_plugin.server.config.logger_format import plugin_logger_handler
from ai_plugin.server.core.entities.message import InitializeMessage
from ai_plugin.server.core.entities.plugin.request import (
    AgentActions,
    ModelActions,
    PluginInvokeType,
    ToolActions,
)
from ai_plugin.server.core.plugin_executor import PluginExecutor
from ai_plugin.server.core.plugin_registration import PluginRegistration
from ai_plugin.server.core.runtime import Session
from ai_plugin.server.core.server.__base.request_reader import RequestReader
from ai_plugin.server.core.server.__base.response_writer import ResponseWriter
from ai_plugin.server.core.server.io_server import IOServer
from ai_plugin.server.core.server.router import Router
from ai_plugin.server.core.server.stdio.request_reader import StdioRequestReader
from ai_plugin.server.core.server.stdio.response_writer import StdioResponseWriter
from ai_plugin.server.core.server.tcp.request_reader import TCPReaderWriter

# 初始化日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class Plugin(IOServer, Router):
    """
    插件主类，继承自IOServer和Router

    负责插件的初始化、配置加载、网络连接管理和请求路由分发
    """

    def __init__(self, config: AlonPluginEnv) -> None:
        """
        初始化插件

        Args:
            config: 插件环境配置
        """
        # 加载插件配置
        self.registration = PluginRegistration(config)

        # 根据安装方式选择合适的流处理方式
        if InstallMethod.Local == config.INSTALL_METHOD:
            request_reader, response_writer = self._launch_local_stream(config)
        elif InstallMethod.Remote == config.INSTALL_METHOD:
            request_reader, response_writer = self._launch_remote_stream(config)
        else:
            raise ValueError("无效的安装方式")

        # 设置默认响应写入器
        self.default_response_writer = response_writer

        # 初始化插件执行器
        self.plugin_executer = PluginExecutor(config, self.registration)

        # 初始化基类
        IOServer.__init__(self, config, request_reader, response_writer)
        Router.__init__(self, request_reader, response_writer)

        # 注册IO路由
        self._register_request_routes()

    def _launch_local_stream(
        self, config: AlonPluginEnv
    ) -> tuple[RequestReader, ResponseWriter | None]:
        """
        启动本地流处理

        Args:
            config: 插件环境配置

        Returns:
            tuple[RequestReader, Optional[ResponseWriter]]: 请求读取器和响应写入器
        """
        reader = StdioRequestReader()
        writer = StdioResponseWriter()
        # 写入插件配置信息
        writer.write(self.registration.configuration.model_dump_json() + "\n\n")

        self._log_configuration()
        return reader, writer

    def _launch_remote_stream(
        self, config: AlonPluginEnv
    ) -> tuple[RequestReader, ResponseWriter | None]:
        """
        启动远程流处理

        Args:
            config: 插件环境配置

        Returns:
            tuple[RequestReader, Optional[ResponseWriter]]: 请求读取器和响应写入器

        Raises:
            ValueError: 当缺少远程安装密钥时抛出
        """
        if not config.REMOTE_INSTALL_KEY:
            raise ValueError("缺少远程安装密钥")

        # 获取远程安装的主机和端口
        install_host, install_port = self._get_remote_install_host_and_port(config)
        logging.debug(f"远程安装到 {install_host}:{install_port}")

        # 创建TCP流连接
        tcp_stream = TCPReaderWriter(
            install_host,
            install_port,
            config.REMOTE_INSTALL_KEY,
            on_connected=lambda: self._initialize_tcp_stream(tcp_stream),
        )

        tcp_stream.launch()

        return tcp_stream, tcp_stream

    def _initialize_tcp_stream(
        self,
        tcp_stream: TCPReaderWriter,
    ):
        """
        初始化TCP流连接

        发送插件的配置信息、工具声明、模型声明、端点声明、智能体策略声明和资源文件

        Args:
            tcp_stream: TCP读写流对象
        """

        class List(RootModel):
            """临时列表模型用于序列化配置数据"""

            root: list[Any]

        # 发送插件清单声明
        tcp_stream.write(
            InitializeMessage(
                type=InitializeMessage.Type.MANIFEST_DECLARATION,
                data=self.registration.configuration.model_dump(),
            ).model_dump_json()
            + "\n\n",
        )

        # 发送工具声明
        if self.registration.tools_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.TOOL_DECLARATION,
                    data=List(root=self.registration.tools_configuration).model_dump(),
                ).model_dump_json()
                + "\n\n",
            )

        # 发送模型声明
        if self.registration.models_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.MODEL_DECLARATION,
                    data=List(root=self.registration.models_configuration).model_dump(),
                ).model_dump_json()
                + "\n\n",
            )

        # 发送端点声明
        if self.registration.endpoints_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.ENDPOINT_DECLARATION,
                    data=List(
                        root=self.registration.endpoints_configuration
                    ).model_dump(),
                ).model_dump_json()
                + "\n\n",
            )

        # 发送智能体策略声明
        if self.registration.agent_strategies_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.AGENT_STRATEGY_DECLARATION,
                    data=List(
                        root=self.registration.agent_strategies_configuration
                    ).model_dump(),
                ).model_dump_json()
                + "\n\n",
            )

        # 发送资源文件（分块传输）
        for file in self.registration.files:
            # 将文件分割成8192字节的块
            chunks = [file.data[i : i + 8192] for i in range(0, len(file.data), 8192)]
            for sequence, chunk in enumerate(chunks):
                tcp_stream.write(
                    InitializeMessage(
                        type=InitializeMessage.Type.ASSET_CHUNK,
                        data=InitializeMessage.AssetChunk(
                            filename=file.filename,
                            data=base64.b64encode(chunk).decode(),
                            end=sequence == len(chunks) - 1,
                        ).model_dump(),
                    ).model_dump_json()
                    + "\n\n",
                )

        # 发送结束标记
        tcp_stream.write(
            InitializeMessage(
                type=InitializeMessage.Type.END,
                data={},
            ).model_dump_json()
            + "\n\n",
        )

        self._log_configuration()

    def _log_configuration(self):
        """
        记录插件配置信息到日志

        输出已安装的工具、模型、端点和智能体的信息
        """
        for tool in self.registration.tools_configuration:
            logger.info(f"已安装工具: {tool.identity.name}")
        for model in self.registration.models_configuration:
            logger.info(f"已安装模型: {model.provider}")
        for endpoint in self.registration.endpoints_configuration:
            logger.info(f"已安装端点: {[e.path for e in endpoint.endpoints]}")
        for agent in self.registration.agent_strategies_configuration:
            logger.info(f"已安装智能体: {agent.identity.name}")

    def _register_request_routes(self):
        """
        注册请求路由

        为不同类型的插件调用请求注册对应的处理函数
        """
        # 注册工具调用路由
        self.register_route(
            self.plugin_executer.invoke_tool,
            lambda data: data.get("type") == PluginInvokeType.Tool.value
            and data.get("action") == ToolActions.InvokeTool.value,
        )

        # 注册工具提供者凭证验证路由
        self.register_route(
            self.plugin_executer.validate_tool_provider_credentials,
            lambda data: data.get("type") == PluginInvokeType.Tool.value
            and data.get("action") == ToolActions.ValidateCredentials.value,
        )

        # 注册智能体策略调用路由
        self.register_route(
            self.plugin_executer.invoke_agent_strategy,
            lambda data: data.get("type") == PluginInvokeType.Agent.value
            and data.get("action") == AgentActions.InvokeAgentStrategy.value,
        )

        # 注册LLM调用路由
        self.register_route(
            self.plugin_executer.invoke_llm,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeLLM.value,
        )

        # 注册获取LLM令牌数量路由
        self.register_route(
            self.plugin_executer.get_llm_num_tokens,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetLLMNumTokens.value,
        )

        # 注册文本嵌入调用路由
        self.register_route(
            self.plugin_executer.invoke_text_embedding,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeTextEmbedding.value,
        )

        # 注册获取文本嵌入令牌数量路由
        self.register_route(
            self.plugin_executer.get_text_embedding_num_tokens,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetTextEmbeddingNumTokens.value,
        )

        # 注册重排序调用路由
        self.register_route(
            self.plugin_executer.invoke_rerank,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeRerank.value,
        )

        # 注册文本转语音调用路由
        self.register_route(
            self.plugin_executer.invoke_tts,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeTTS.value,
        )

        # 注册获取TTS模型声音列表路由
        self.register_route(
            self.plugin_executer.get_tts_model_voices,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetTTSVoices.value,
        )

        # 注册语音转文本调用路由
        self.register_route(
            self.plugin_executer.invoke_speech_to_text,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeSpeech2Text.value,
        )

        # 注册内容审核调用路由
        self.register_route(
            self.plugin_executer.invoke_moderation,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeModeration.value,
        )

        # 注册模型提供者凭证验证路由
        self.register_route(
            self.plugin_executer.validate_model_provider_credentials,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.ValidateProviderCredentials.value,
        )

        # 注册模型凭证验证路由
        self.register_route(
            self.plugin_executer.validate_model_credentials,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.ValidateModelCredentials.value,
        )

        # 注册获取AI模型结构路由
        self.register_route(
            self.plugin_executer.get_ai_model_schemas,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetAIModelSchemas.value,
        )

    def _execute_request(
        self,
        session_id: str,
        data: dict,
        reader: RequestReader,
        writer: ResponseWriter,
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ):
        """
        接收请求并执行

        Args:
            session_id: 会话ID，每个请求都有唯一标识
            data: 请求数据
            reader: 请求读取器
            writer: 响应写入器
            conversation_id: 对话ID（可选）
            message_id: 消息ID（可选）
            app_id: 应用ID（可选）
            endpoint_id: 端点ID（可选）
        """
        # 创建会话对象
        session = Session(
            session_id=session_id,
            executor=self.executer,
            reader=reader,
            writer=writer,
            install_method=self.config.INSTALL_METHOD,
            dify_plugin_daemon_url=self.config.DIFY_PLUGIN_DAEMON_URL,
            conversation_id=conversation_id,
            message_id=message_id,
            app_id=app_id,
            endpoint_id=endpoint_id,
        )

        # 分发请求并获取响应
        response = self.dispatch(session, data)
        if response:
            if isinstance(response, Generator):
                # 处理流式响应
                for message in response:
                    if isinstance(message, ToolInvokeMessage) and isinstance(
                        message.message,
                        ToolInvokeMessage.BlobMessage,
                    ):
                        # 将二进制数据转换为文件块
                        id_ = uuid.uuid4().hex
                        blob = message.message.blob
                        message.message.blob = id_.encode("utf-8")

                        # 将二进制数据分割成8192字节的块
                        chunks = [blob[i : i + 8192] for i in range(0, len(blob), 8192)]
                        for sequence, chunk in enumerate(chunks):
                            writer.session_message(
                                session_id=session_id,
                                data=writer.stream_object(
                                    data=ToolInvokeMessage(
                                        type=ToolInvokeMessage.MessageType.BLOB_CHUNK,
                                        message=ToolInvokeMessage.BlobChunkMessage(
                                            id=id_,
                                            sequence=sequence,
                                            total_length=len(blob),
                                            blob=chunk,
                                            end=False,
                                        ),
                                        meta=message.meta,
                                    ),
                                ),
                            )

                        # 发送文件流结束标记
                        writer.session_message(
                            session_id=session_id,
                            data=writer.stream_object(
                                data=ToolInvokeMessage(
                                    type=ToolInvokeMessage.MessageType.BLOB_CHUNK,
                                    message=ToolInvokeMessage.BlobChunkMessage(
                                        id=id_,
                                        sequence=len(chunks),
                                        total_length=len(blob),
                                        blob=b"",
                                        end=True,
                                    ),
                                    meta=message.meta,
                                ),
                            ),
                        )
                    else:
                        # 发送普通消息
                        writer.session_message(
                            session_id=session_id,
                            data=writer.stream_object(data=message),
                        )
            else:
                # 处理单次响应
                writer.session_message(
                    session_id=session_id,
                    data=writer.stream_object(data=response),
                )

    @staticmethod
    def _get_remote_install_host_and_port(config: AlonPluginEnv) -> tuple[str, int]:
        """
        获取远程安装的主机和端口

        Args:
            config: 插件环境配置

        Returns:
            tuple[str, int]: 主机地址和端口号

        Raises:
            ValueError: 当远程安装URL格式无效时抛出
        """
        install_url = config.REMOTE_INSTALL_URL
        if install_url is not None:
            if ":" in install_url:
                url = URL(install_url)
                if url.host and url.port:
                    # 处理带协议前缀的URL
                    host = url.host
                    port = url.port
                else:
                    # 处理"host:port"格式
                    split = install_url.split(":")
                    host = split[0]
                    port = int(split[1])
            else:
                raise ValueError(
                    f'无效的远程安装URL {install_url}，应该使用"host:port"格式'
                )
        else:
            # 使用配置中的主机和端口
            host = config.REMOTE_INSTALL_HOST
            port = config.REMOTE_INSTALL_PORT

        return host, port
