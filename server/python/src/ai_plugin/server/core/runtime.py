import uuid
from collections.abc import Generator, Mapping
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, TypeAdapter
from yarl import URL

from ai_plugin.server.config.config import InstallMethod
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamBase,
    PluginInStreamEvent,
)
from ai_plugin.server.core.server.__base.request_reader import RequestReader
from ai_plugin.server.core.server.__base.response_writer import ResponseWriter
from ai_plugin.server.core.server.tcp.request_reader import TCPReaderWriter

#################################################
# 会话管理
#################################################


class ModelInvocations:
    """
    模型调用管理类

    包含各种模型类型的调用接口，提供统一的模型服务访问入口
    """

    def __init__(self, session: "Session") -> None:
        """
        初始化模型调用管理器

        Args:
            session: 会话实例
        """
        from ai_plugin.server.invocations.model.llm import (
            LLMInvocation,
            SummaryInvocation,
        )
        from ai_plugin.server.invocations.model.moderation import ModerationInvocation
        from ai_plugin.server.invocations.model.rerank import RerankInvocation
        from ai_plugin.server.invocations.model.speech2text import (
            Speech2TextInvocation,
        )
        from ai_plugin.server.invocations.model.text_embedding import (
            TextEmbeddingInvocation,
        )
        from ai_plugin.server.invocations.model.tts import TTSInvocation

        self.llm = LLMInvocation(session)
        self.text_embedding = TextEmbeddingInvocation(session)
        self.rerank = RerankInvocation(session)
        self.speech2text = Speech2TextInvocation(session)
        self.tts = TTSInvocation(session)
        self.moderation = ModerationInvocation(session)
        self.summary = SummaryInvocation(session)


class AppInvocations:
    """
    应用调用管理类

    提供各种应用调用接口，包括聊天、补全、工作流等功能
    """

    def __init__(self, session: "Session"):
        """
        初始化应用调用管理器

        Args:
            session: 会话实例
        """
        from ai_plugin.server.invocations.app import FetchAppInvocation
        from ai_plugin.server.invocations.app.chat import ChatAppInvocation
        from ai_plugin.server.invocations.app.completion import (
            CompletionAppInvocation,
        )
        from ai_plugin.server.invocations.app.workflow import WorkflowAppInvocation

        self.chat = ChatAppInvocation(session)
        self.completion = CompletionAppInvocation(session)
        self.workflow = WorkflowAppInvocation(session)
        self.fetch_app_invocation = FetchAppInvocation(session)

    def fetch_app(self, app_id: str) -> Mapping:
        """
        获取应用信息

        Args:
            app_id: 应用ID

        Returns:
            应用信息映射
        """
        return self.fetch_app_invocation.get(app_id)


class WorkflowNodeInvocations:
    """
    工作流节点调用管理类

    提供各种工作流节点的调用接口
    """

    def __init__(self, session: "Session"):
        """
        初始化工作流节点调用管理器

        Args:
            session: 会话实例
        """
        from ai_plugin.server.invocations.workflow_node.parameter_extractor import (
            ParameterExtractorNodeInvocation,
        )
        from ai_plugin.server.invocations.workflow_node.question_classifier import (
            QuestionClassifierNodeInvocation,
        )

        self.question_classifier = QuestionClassifierNodeInvocation(session)
        self.parameter_extractor = ParameterExtractorNodeInvocation(session)


class Session:
    """
    会话管理类

    管理插件运行时的会话状态，提供统一的调用接口和上下文信息
    """

    def __init__(
        self,
        session_id: str,
        executor: ThreadPoolExecutor,
        reader: RequestReader,
        writer: ResponseWriter,
        install_method: InstallMethod | None = None,
        dify_plugin_daemon_url: str | None = None,
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ) -> None:
        """
        初始化会话

        Args:
            session_id: 会话ID
            executor: 线程池执行器
            reader: 请求读取器
            writer: 响应写入器
            install_method: 安装方式，可选
            dify_plugin_daemon_url: Dify插件守护进程URL，可选
            conversation_id: 对话ID，可选
            message_id: 消息ID，可选
            app_id: 应用ID，可选
            endpoint_id: 端点ID，可选
        """
        # 当前会话ID
        self.session_id: str = session_id

        # 线程池执行器
        self._executor: ThreadPoolExecutor = executor

        # 请求读取器和响应写入器
        self.reader: RequestReader = reader
        self.writer: ResponseWriter = writer

        # 对话ID
        self.conversation_id: str | None = conversation_id

        # 消息ID
        self.message_id: str | None = message_id

        # 应用ID
        self.app_id: str | None = app_id

        # 端点ID
        self.endpoint_id: str | None = endpoint_id

        # 安装方式
        self.install_method: InstallMethod | None = install_method

        # Dify插件守护进程URL
        self.dify_plugin_daemon_url: str | None = dify_plugin_daemon_url

        # 注册调用接口
        self._register_invocations()

    def _register_invocations(self) -> None:
        """
        注册各种调用接口

        初始化模型、工具、应用、工作流节点、存储、文件等调用接口
        """
        from ai_plugin.server.invocations.file import File
        from ai_plugin.server.invocations.storage import StorageInvocation
        from ai_plugin.server.invocations.tool import ToolInvocation

        # 模型调用接口
        self.model = ModelInvocations(self)
        # 工具调用接口
        self.tool = ToolInvocation(self)
        # 应用调用接口
        self.app = AppInvocations(self)
        # 工作流节点调用接口
        self.workflow_node = WorkflowNodeInvocations(self)
        # 存储调用接口
        self.storage = StorageInvocation(self)
        # 文件调用接口
        self.file = File(self)

    @classmethod
    def empty_session(cls) -> "Session":
        """
        创建空会话

        Returns:
            空的会话实例，用于测试或占位
        """
        return cls(
            session_id="",
            executor=ThreadPoolExecutor(),
            reader=TCPReaderWriter(host="", port=0, key=""),
            writer=TCPReaderWriter(host="", port=0, key=""),
            install_method=None,
            dify_plugin_daemon_url=None,
        )


#################################################
# 反向调用请求
#################################################


class BackwardsInvocationResponseEvent(BaseModel):
    """
    反向调用响应事件

    定义反向调用响应的事件类型和数据结构
    """

    class Event(Enum):
        """事件类型枚举"""

        response = "response"  # 响应事件
        Error = "error"  # 错误事件
        End = "end"  # 结束事件

    # 反向请求ID
    backwards_request_id: str
    # 事件类型
    event: Event
    # 消息内容
    message: str
    # 附加数据
    data: dict | None


class BackwardsInvocation[T: (BaseModel | dict | str)]:
    """
    反向调用基类

    提供向Dify系统发起反向调用的基础功能
    """

    def __init__(
        self,
        session: Session | None = None,
    ) -> None:
        """
        初始化反向调用

        Args:
            session: 会话实例，可选
        """
        self.session = session

    def _generate_backwards_request_id(self):
        """
        生成反向请求ID

        Returns:
            唯一的请求ID字符串
        """
        return uuid.uuid4().hex

    def _backwards_invoke(
        self,
        type: InvokeType,
        data_type: type[T],
        data: dict,
    ) -> Generator[T, None, None]:
        """
        根据当前运行时类型执行反向调用Dify

        Args:
            type: 调用类型
            data_type: 数据类型
            data: 调用数据

        Returns:
            响应数据生成器
        """
        backwards_request_id = self._generate_backwards_request_id()

        if not self.session:
            raise Exception("当前工具运行时不支持反向调用")
        if self.session.install_method in [InstallMethod.Local, InstallMethod.Remote]:
            return self._full_duplex_backwards_invoke(
                backwards_request_id, type, data_type, data
            )
        return self._http_backwards_invoke(backwards_request_id, type, data_type, data)

    def _line_converter_wrapper(
        self,
        generator: Generator[PluginInStreamBase | None, None, None],
        data_type: type[T],
    ) -> Generator[T, None, None]:
        """
        将字符串转换为指定类型T

        Args:
            generator: 输入流生成器
            data_type: 目标数据类型

        Yields:
            转换后的数据
        """
        empty_response_count = 0

        for chunk in generator:
            """
            从输入流接收响应，最多等待60秒
            """
            if chunk is None:
                empty_response_count += 1
                # 如果250秒内没有响应，则中断
                if empty_response_count >= 250:
                    raise Exception("调用退出时没有响应")
                continue

            event = BackwardsInvocationResponseEvent(**chunk.data)
            if event.event == BackwardsInvocationResponseEvent.Event.End:
                break

            if event.event == BackwardsInvocationResponseEvent.Event.Error:
                raise Exception(event.message)

            if event.data is None:
                break

            empty_response_count = 0
            try:
                yield data_type(**event.data)
            except Exception as e:
                raise Exception(f"解析响应失败: {e!s}") from e

    def _http_backwards_invoke(
        self,
        backwards_request_id: str,
        type: InvokeType,
        data_type: type[T],
        data: dict,
    ) -> Generator[T, None, None]:
        """
        通过HTTP执行反向调用

        Args:
            backwards_request_id: 反向请求ID
            type: 调用类型
            data_type: 数据类型
            data: 调用数据

        Yields:
            响应数据
        """
        if not self.session or not self.session.dify_plugin_daemon_url:
            raise Exception("当前工具运行时不支持反向调用")

        url = (
            URL(self.session.dify_plugin_daemon_url)
            / "backwards-invocation"
            / "transaction"
        )
        headers = {
            "Dify-Plugin-Session-ID": self.session.session_id,
        }

        payload = self.session.writer.session_message_text(
            session_id=self.session.session_id,
            data=self.session.writer.stream_invoke_object(
                data={
                    "type": type.value,
                    "backwards_request_id": backwards_request_id,
                    "request": data,
                },
            ),
        )

        with (
            httpx.Client() as client,
            client.stream(
                method="POST",
                url=str(url),
                headers=headers,
                content=payload,
                timeout=(
                    300,
                    300,
                    300,
                    300,
                ),  # 连接、读取、写入和池的300秒超时
            ) as response,
        ):

            def generator():
                for line in response.iter_lines():
                    if not line:
                        continue

                    data = TypeAdapter(dict[str, Any]).validate_json(line)
                    yield PluginInStreamBase(
                        session_id=data["session_id"],
                        event=PluginInStreamEvent.value_of(data["event"]),
                        data=data["data"],
                    )

            yield from self._line_converter_wrapper(generator(), data_type)

    def _full_duplex_backwards_invoke(
        self,
        backwards_request_id: str,
        type: InvokeType,
        data_type: type[T],
        data: dict,
    ) -> Generator[T, None, None]:
        """
        通过全双工连接执行反向调用

        Args:
            backwards_request_id: 反向请求ID
            type: 调用类型
            data_type: 数据类型
            data: 调用数据

        Yields:
            响应数据
        """
        if not self.session:
            raise Exception("当前工具运行时不支持反向调用")

        self.session.writer.session_message(
            session_id=self.session.session_id,
            data=self.session.writer.stream_invoke_object(
                data={
                    "type": type.value,
                    "backwards_request_id": backwards_request_id,
                    "request": data,
                },
            ),
        )

        def filter(data: PluginInStream) -> bool:
            return (
                data.event == PluginInStreamEvent.BackwardInvocationResponse
                and data.data.get("backwards_request_id") == backwards_request_id
            )

        with self.session.reader.read(filter) as reader:
            yield from self._line_converter_wrapper(
                reader.read(timeout_for_round=1), data_type
            )
