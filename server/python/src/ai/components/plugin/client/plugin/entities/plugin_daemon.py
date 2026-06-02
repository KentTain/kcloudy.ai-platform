from pydantic import BaseModel, Field

from ai_plugin.sdk.entities.provider_config import ProviderConfig
from ai_plugin.sdk.entities.tool import ToolProviderIdentity
from ai_plugin.sdk.interfaces.agent import ToolEntity


class ToolProviderEntity(BaseModel):
    identity: ToolProviderIdentity
    plugin_id: str | None = None
    credentials_schema: list[ProviderConfig] = Field(default_factory=list)


class ToolProviderEntityWithPlugin(ToolProviderEntity):
    tools: list[ToolEntity] = Field(default_factory=list)


class PluginToolProviderEntity(BaseModel):
    """
    插件工具提供者实体类

    表示由插件提供的工具服务的完整信息
    """

    provider: str  # 提供者名称
    plugin_unique_identifier: str  # 插件唯一标识符
    plugin_id: str  # 插件ID
    declaration: ToolProviderEntityWithPlugin  # 工具提供者声明


class PluginDaemonInnerError(Exception):
    """
    插件守护进程内部错误异常类

    表示插件守护进程内部发生的错误
    """

    code: int  # 错误码
    message: str  # 错误消息

    def __init__(self, code: int, message: str):
        """
        初始化内部错误

        :param code: 错误码
        :param message: 错误消息
        """
        self.code = code
        self.message = message
