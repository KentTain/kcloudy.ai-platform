"""
插件通讯协议封装
统一管理插件与引擎之间的通讯协议、消息格式、错误处理等
"""

import uuid
from typing import Any

import orjson
from loguru import logger
from pydantic import BaseModel

from ai_plugin.server.core.entities.plugin.io import PluginInStreamEvent
from ai_plugin.server.core.server.__base.writer_entities import StreamOutputMessage
from framework.utils.json_util import orjson_default


class PluginInStream(BaseModel):
    """插件输入流基础类"""

    session_id: str
    event: PluginInStreamEvent
    data: dict[str, Any]
    conversation_id: str | None = None
    message_id: str | None = None
    app_id: str | None = None
    endpoint_id: str | None = None

    def __init__(
        self,
        session_id: str,
        event: PluginInStreamEvent,
        data: dict[str, Any],
        conversation_id: str | None = None,
        message_id: str | None = None,
        app_id: str | None = None,
        endpoint_id: str | None = None,
    ):
        super().__init__(
            session_id=session_id,
            event=event,
            data=data,
            conversation_id=conversation_id,
            message_id=message_id,
            app_id=app_id,
            endpoint_id=endpoint_id,
        )


class PluginMessageProtocol:
    """插件消息协议 - 使用实体类"""

    @staticmethod
    def create_request_message(
        invoke_request: dict[str, Any], session_id: str | None = None
    ) -> PluginInStream:
        """创建请求消息"""
        return PluginInStream(
            session_id=session_id or f"session_{uuid.uuid4()}",
            event=PluginInStreamEvent.Request,
            data=invoke_request,
            conversation_id=invoke_request.get("conversation_id"),
            message_id=invoke_request.get("message_id"),
            app_id=invoke_request.get("app_id"),
            endpoint_id=invoke_request.get("endpoint_id"),
        )

    @staticmethod
    def _mask_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
        """脱敏处理敏感数据，用于日志打印"""
        masked_data = data.copy()

        # 处理credentials字段
        if "credentials" in masked_data and isinstance(
            masked_data["credentials"], dict
        ):
            credentials = masked_data["credentials"].copy()
            for key, value in credentials.items():
                if isinstance(value, str) and value:
                    # 保留前3个字符和后3个字符，中间用***代替
                    if len(value) > 8:
                        credentials[key] = f"{value[:3]}***{value[-3:]}"
                    else:
                        credentials[key] = "***"
            masked_data["credentials"] = credentials

        return masked_data

    @staticmethod
    def to_bytes(request: PluginInStream) -> bytes:
        """转换为JSON格式的消息"""

        # 序列化实际要发送的数据
        json_str = request.model_dump_json()

        # 创建脱敏版本用于日志打印
        try:
            # 直接从request对象获取字典，避免序列化-反序列化
            request_dict = request.model_dump()
            if "data" in request_dict:
                request_dict["data"] = PluginMessageProtocol._mask_sensitive_data(
                    request_dict["data"]
                )
            masked_json_str = orjson.dumps(request_dict, default=orjson_default).decode(
                "utf-8"
            )
            logger.debug(f"待发送消息: {masked_json_str}")
        except Exception as e:
            # 如果脱敏处理失败，记录错误但不影响正常流程
            logger.warning(f"消息脱敏处理失败: {e}")
            logger.debug(f"待发送消息: {json_str}")

        # 添加换行符才能被流式读取，插件端会判断该字符串是否以\n结尾来判断是否结束
        return (json_str + "\n").encode("utf-8")

    @staticmethod
    def parse_message(message_str: str) -> StreamOutputMessage | dict | None:
        """解析消息字符串"""

        try:
            data = orjson.loads(message_str)
            if "event" in data:
                return StreamOutputMessage(**data)
            else:
                return data
        except Exception as e:
            logger.error(f"解析消息失败: {e}, message_str: {message_str}")
            return None


class PluginCommunicationError(Exception):
    """插件通讯异常"""

    def __init__(self, message: str, data: dict | None = None):
        super().__init__(message)
        self.data = data


class PluginTimeoutError(PluginCommunicationError):
    """插件超时异常"""

    pass


class PluginError(Exception):
    """插件错误，例如插件退出等，需要重启插件"""

    pass
