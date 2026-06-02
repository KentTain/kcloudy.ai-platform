from enum import Enum

from pydantic import BaseModel


class SessionMessage(BaseModel):
    """
    会话消息类

    表示插件会话中的消息，包含类型和数据
    """

    class Type(Enum):
        """消息类型枚举"""

        STREAM = "stream"  # 流式消息
        INVOKE = "invoke"  # 调用消息
        END = "end"  # 结束消息
        ERROR = "error"  # 错误消息

    # 消息类型
    type: Type
    # 消息数据
    data: dict

    def to_dict(self):
        """
        转换为字典格式

        Returns:
            dict: 包含type和data的字典
        """
        return {"type": self.type.value, "data": self.data}


class InitializeMessage(BaseModel):
    """
    初始化消息类

    用于插件初始化过程中的各种声明和配置消息
    """

    class Type(Enum):
        """初始化消息类型枚举"""

        HANDSHAKE = "handshake"  # 握手消息
        ASSET_CHUNK = "asset_chunk"  # 资源块消息
        MANIFEST_DECLARATION = "manifest_declaration"  # 清单声明消息
        TOOL_DECLARATION = "tool_declaration"  # 工具声明消息
        MODEL_DECLARATION = "model_declaration"  # 模型声明消息
        ENDPOINT_DECLARATION = "endpoint_declaration"  # 端点声明消息
        AGENT_STRATEGY_DECLARATION = "agent_strategy_declaration"  # 代理策略声明消息
        END = "end"  # 结束消息

    class AssetChunk(BaseModel):
        """
        资源块类

        用于传输大文件的分块数据
        """

        filename: str  # 文件名
        data: str  # base64编码的数据
        end: bool  # 是否为最后一块

    class Key(BaseModel):
        """
        密钥类

        用于传输密钥信息
        """

        key: str  # 密钥字符串

    # 消息类型
    type: Type
    # 消息数据
    data: dict | list
