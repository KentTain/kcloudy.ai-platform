from abc import ABC, abstractmethod
from collections.abc import Generator, Mapping
from typing import Any, Optional, final

from werkzeug import Request

from ai_plugin.sdk.entities.agent import AgentInvokeMessage
from ai_plugin.sdk.entities.provider_config import LogMetadata
from ai_plugin.sdk.entities.tool import (
    ToolInvokeMessage,
    ToolParameter,
    ToolRuntime,
    ToolSelector,
)
from ai_plugin.sdk.file.constants import (
    DIFY_FILE_IDENTITY,
    DIFY_TOOL_SELECTOR_IDENTITY,
)
from ai_plugin.sdk.file.entities import FileType
from ai_plugin.sdk.file.file import File
from ai_plugin.server.core.runtime import Session


class ToolLike[T: (ToolInvokeMessage | AgentInvokeMessage)](ABC):
    """工具类基类，提供创建各种类型消息的通用方法"""

    response_type: type[T]

    ############################################################
    #                    仅供插件实现使用                        #
    ############################################################

    def create_text_message(self, text: str) -> T:
        """
        创建文本消息

        :param text: 文本内容
        :return: 文本消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.TEXT,
            message=ToolInvokeMessage.TextMessage(text=text),
        )

    def create_json_message(self, json: Mapping | list) -> T:
        """
        创建JSON消息

        :param json: JSON对象或列表
        :return: JSON消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.JSON,
            message=ToolInvokeMessage.JsonMessage(json_object=json),
        )

    def create_image_message(self, image_url: str) -> T:
        """
        创建图片消息

        :param image_url: 图片的URL地址
        :return: 图片消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.IMAGE,
            message=ToolInvokeMessage.TextMessage(text=image_url),
        )

    def create_link_message(self, link: str) -> T:
        """
        创建链接消息

        :param link: 链接的URL地址
        :return: 链接消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.LINK,
            message=ToolInvokeMessage.TextMessage(text=link),
        )

    def create_blob_message(self, blob: bytes, meta: dict | None = None) -> T:
        """
        创建二进制数据消息

        :param blob: 二进制数据
        :param meta: 元数据（可选）
        :return: 二进制数据消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.BLOB,
            message=ToolInvokeMessage.BlobMessage(blob=blob),
            meta=meta,
        )

    def create_variable_message(self, variable_name: str, variable_value: Any) -> T:
        """
        创建变量消息

        :param variable_name: 变量名称
        :param variable_value: 变量值
        :return: 变量消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.VARIABLE,
            message=ToolInvokeMessage.VariableMessage(
                variable_name=variable_name, variable_value=variable_value
            ),
        )

    def create_stream_variable_message(
        self, variable_name: str, variable_value: str
    ) -> T:
        """
        创建流式变量消息，该消息将以流的形式传输到前端

        注意：变量值应该是字符串类型，目前只支持字符串的流式传输

        :param variable_name: 变量名称
        :param variable_value: 变量值
        :return: 流式变量消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.VARIABLE,
            message=ToolInvokeMessage.VariableMessage(
                variable_name=variable_name,
                variable_value=variable_value,
                stream=True,
            ),
        )

    def create_log_message(
        self,
        label: str,
        data: Mapping[str, Any],
        status: ToolInvokeMessage.LogMessage.LogStatus = ToolInvokeMessage.LogMessage.LogStatus.SUCCESS,
        parent: T | None = None,
        metadata: Mapping[LogMetadata, Any] | None = None,
    ) -> T:
        """
        创建日志消息

        :param label: 日志标签
        :param data: 日志数据
        :param status: 日志状态，默认为成功
        :param parent: 父级日志消息（可选）
        :param metadata: 元数据（可选）
        :return: 日志消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.LOG,
            message=ToolInvokeMessage.LogMessage(
                label=label,
                data=data,
                status=status,
                parent_id=parent.message.id
                if parent and isinstance(parent.message, ToolInvokeMessage.LogMessage)
                else None,
                metadata=metadata,
            ),
        )

    def create_retriever_resource_message(
        self,
        retriever_resources: list[
            ToolInvokeMessage.RetrieverResourceMessage.RetrieverResource
        ],
        context: str,
    ) -> T:
        """
        创建检索器资源消息

        :param retriever_resources: 检索器资源列表
        :param context: 上下文信息
        :return: 检索器资源消息对象
        """
        return self.response_type(
            type=ToolInvokeMessage.MessageType.RETRIEVER_RESOURCES,
            message=ToolInvokeMessage.RetrieverResourceMessage(
                retriever_resources=retriever_resources,
                context=context,
            ),
        )

    def finish_log_message(
        self,
        log: T,
        status: ToolInvokeMessage.LogMessage.LogStatus = ToolInvokeMessage.LogMessage.LogStatus.SUCCESS,
        error: str | None = None,
        data: Mapping[str, Any] | None = None,
        metadata: Mapping[LogMetadata, Any] | None = None,
    ) -> T:
        """
        标记日志消息为完成状态

        :param log: 要完成的日志消息
        :param status: 最终状态，默认为成功
        :param error: 错误信息（可选）
        :param data: 最终数据（可选）
        :param metadata: 元数据（可选）
        :return: 更新后的日志消息对象
        """
        assert isinstance(log.message, ToolInvokeMessage.LogMessage)
        return self.response_type(
            type=ToolInvokeMessage.MessageType.LOG,
            message=ToolInvokeMessage.LogMessage(
                id=log.message.id,
                label=log.message.label,
                data=data or log.message.data,
                status=status,
                parent_id=log.message.parent_id,
                error=error,
                metadata=metadata or log.message.metadata,
            ),
        )

    def _get_runtime_parameters(self) -> list[ToolParameter]:
        """
        获取工具的运行时参数

        :return: 运行时参数列表
        """
        return []

    @classmethod
    def _is_get_runtime_parameters_overridden(cls) -> bool:
        """
        检查子类是否重写了_get_runtime_parameters方法

        :return: 如果已重写返回True，否则返回False
        """
        return "_get_runtime_parameters" in cls.__dict__

    @classmethod
    def _convert_parameters(cls, tool_parameters: dict) -> dict:
        """
        将参数转换为正确的类型

        :param tool_parameters: 工具参数字典
        :return: 转换后的参数字典
        """
        for parameter, value in tool_parameters.items():
            if (
                isinstance(value, dict)
                and value.get("dify_model_identity") == DIFY_FILE_IDENTITY
            ):
                tool_parameters[parameter] = File(
                    url=value["url"],
                    mime_type=value.get("mime_type"),
                    type=FileType(value.get("type")),
                    filename=value.get("filename"),
                    extension=value.get("extension"),
                    size=value.get("size"),
                )
            elif isinstance(value, list) and all(
                isinstance(item, dict)
                and item.get("dify_model_identity") == DIFY_FILE_IDENTITY
                for item in value
            ):
                tool_parameters[parameter] = [
                    File(
                        url=item["url"],
                        mime_type=item.get("mime_type"),
                        type=FileType(item.get("type")),
                        filename=item.get("filename"),
                        extension=item.get("extension"),
                        size=item.get("size"),
                    )
                    for item in value
                ]
            elif (
                isinstance(value, dict)
                and value.get("dify_model_identity") == DIFY_TOOL_SELECTOR_IDENTITY
            ):
                tool_parameters[parameter] = ToolSelector.model_validate(value)
            elif isinstance(value, list) and all(
                isinstance(item, dict)
                and item.get("dify_model_identity") == DIFY_TOOL_SELECTOR_IDENTITY
                for item in value
            ):
                tool_parameters[parameter] = [
                    ToolSelector.model_validate(item) for item in value
                ]

        return tool_parameters


class ToolProvider:
    """工具提供者基类"""

    def validate_credentials(self, credentials: dict):
        """
        验证工具提供者凭证

        :param credentials: 凭证字典
        """
        return self._validate_credentials(credentials)

    def _validate_credentials(self, credentials: dict):
        """
        验证凭证的内部实现方法（由子类实现）

        :param credentials: 凭证字典
        """
        raise NotImplementedError("This method should be implemented by a subclass")

    def oauth_get_authorization_url(self, system_credentials: Mapping[str, Any]) -> str:
        """
        获取OAuth授权URL

        :param system_credentials: 系统凭证
        :return: 授权URL
        """
        return self._oauth_get_authorization_url(system_credentials)

    def _oauth_get_authorization_url(
        self, system_credentials: Mapping[str, Any]
    ) -> str:
        """
        获取OAuth授权URL的内部实现方法（由子类实现）

        :param system_credentials: 系统凭证
        :return: 授权URL
        """
        raise NotImplementedError("This method should be implemented by a subclass")

    def oauth_get_credentials(
        self, system_credentials: Mapping[str, Any], request: Request
    ) -> Mapping[str, Any]:
        """
        通过OAuth请求获取凭证

        :param system_credentials: 系统凭证
        :param request: HTTP请求对象
        :return: 获取到的凭证
        """
        return self._oauth_get_credentials(system_credentials, request)

    def _oauth_get_credentials(
        self, system_credentials: Mapping[str, Any], request: Request
    ) -> Mapping[str, Any]:
        """
        通过OAuth请求获取凭证的内部实现方法（由子类实现）

        :param system_credentials: 系统凭证
        :param request: HTTP请求对象
        :return: 获取到的凭证
        """
        raise NotImplementedError("This method should be implemented by a subclass")


class Tool(ToolLike[ToolInvokeMessage]):
    """工具基类，所有具体工具都应继承此类"""

    runtime: ToolRuntime
    session: Session

    @final
    def __init__(
        self,
        runtime: ToolRuntime,
        session: Session,
    ):
        """
        初始化工具实例

        注意：此方法已标记为final，请不要重写

        :param runtime: 工具运行时环境
        :param session: 会话对象
        """
        self.runtime = runtime
        self.session = session
        self.response_type = ToolInvokeMessage

    @classmethod
    def from_credentials(
        cls,
        credentials: dict,
        user_id: str | None = None,
    ):
        """
        从凭证创建工具实例

        :param credentials: 凭证字典
        :param user_id: 用户ID（可选）
        :return: 工具实例
        """
        return cls(
            runtime=ToolRuntime(
                credentials=credentials,
                user_id=user_id,
                session_id=None,
            ),
            session=Session.empty_session(),
        )

    @abstractmethod
    def _invoke(
        self, tool_parameters: dict
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        工具调用的具体实现方法（由子类实现）

        :param tool_parameters: 工具参数
        :return: 工具调用消息生成器
        """
        raise NotImplementedError("This method should be implemented by a subclass")

    ############################################################
    #                   仅供执行器使用                          #
    ############################################################

    def invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用工具

        :param tool_parameters: 工具参数
        :return: 工具调用消息生成器
        """
        # 将参数转换为正确的类型
        tool_parameters = self._convert_parameters(tool_parameters)
        return self._invoke(tool_parameters)

    def get_runtime_parameters(self) -> list[ToolParameter]:
        """
        获取运行时参数

        :return: 运行时参数列表
        """
        return self._get_runtime_parameters()
