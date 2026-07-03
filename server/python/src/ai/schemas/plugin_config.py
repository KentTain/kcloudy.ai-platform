"""插件配置相关 Schema

提供插件配置、测试、启动、停止等操作的请求和响应模型。

注意：这些 Schema 用于新的插件配置接口（路径参数版本），与现有的接口（Query 参数版本）分离。
"""

from __future__ import annotations

from framework.schemas import BaseModel


class PluginConfigRequest(BaseModel):
    """插件配置请求"""

    plugin_config: dict | None = None
    """插件能力配置，如 API Key、Endpoint 等"""

    runtime_config: dict | None = None
    """运行时配置，如超时时间、重试次数等"""


class PluginConfigResponse(BaseModel):
    """插件配置响应"""

    plugin_id: str
    """插件 ID"""

    validated: bool | None = None
    """配置验证状态：null=未测试, true=验证通过, false=验证失败"""

    message: str | None = None
    """配置保存或验证的消息"""


class PluginTestRequest(BaseModel):
    """插件测试请求"""

    pass  # 无需额外参数，使用已保存的配置测试


class PluginTestResponse(BaseModel):
    """插件测试响应"""

    plugin_id: str
    """插件 ID"""

    validated: bool
    """配置验证结果"""

    message: str
    """验证结果消息"""


class PluginStartRequest(BaseModel):
    """插件启动请求"""

    pass  # 无需额外参数


class PluginStartResponse(BaseModel):
    """插件启动响应"""

    plugin_id: str
    """插件 ID"""

    status: str
    """插件状态：ACTIVE"""

    port: int | None = None
    """运行端口"""

    warning: str | None = None
    """警告信息（如配置未验证）"""


class PluginStopRequest(BaseModel):
    """插件停止请求"""

    pass  # 无需额外参数


class PluginStopResponse(BaseModel):
    """插件停止响应"""

    plugin_id: str
    """插件 ID"""

    status: str
    """插件状态：INACTIVE"""
