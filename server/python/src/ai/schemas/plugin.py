"""
插件相关 Pydantic 模型

包含插件配置、插件信息、插件凭证等请求/响应模型。
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PluginConfig(BaseModel):
    """
    插件配置类

    负责加载和管理插件的配置、工具、模型、代理策略等组件。
    """

    # 插件基础配置
    configuration: dict[str, Any] = Field(description="插件基础配置")

    # 工具提供者配置列表
    tools_configuration: list[dict[str, Any]] | None = Field(
        default=None, description="工具提供者配置列表"
    )

    # 代理策略提供者配置列表
    agent_strategies_configuration: list[dict[str, Any]] | None = Field(
        default=None,
        description="代理策略提供者配置列表",
    )

    # 模型提供者配置列表
    models_configuration: list[dict[str, Any]] | None = Field(
        default=None,
        description="模型提供者配置列表",
    )


class PluginInfoVo(BaseModel):
    """插件信息"""

    model_config = ConfigDict(from_attributes=True)

    plugin_id: str = Field(description="插件ID", examples=["author/plugin_name"])
    plugin_name: str = Field(description="插件名称", examples=["Plugin Name"])
    version: str = Field(description="插件版本", examples=["1.0.0"])
    author: str = Field(description="作者", examples=["author"])
    description: str | None = Field(default=None, description="插件描述")
    icon: str | None = Field(default=None, description="图标")
    status: str = Field(description="插件状态", examples=["running"])
    plugin_type: str = Field(description="插件类型", examples=["model"])
    runtime_type: str = Field(description="运行时类型", examples=["local"])
    auto_start: bool = Field(description="是否自动启动")
    installed_at: str | None = Field(default=None, description="安装时间")
    last_started_at: str | None = Field(default=None, description="最后启动时间")
    last_stopped_at: str | None = Field(default=None, description="最后停止时间")
    last_accessed_at: str | None = Field(default=None, description="最后访问时间")
    process_id: int | None = Field(default=None, description="进程ID")
    port: int | None = Field(default=None, description="运行端口")
    call_count: int = Field(description="调用次数", examples=[100])
    error_count: int = Field(description="错误次数", examples=[0])
    last_error: str | None = Field(default=None, description="最后错误信息")


class PluginListResponseVo(BaseModel):
    """插件列表响应"""

    plugins: list[PluginInfoVo] = Field(description="插件列表")
    total: int = Field(description="总数量", examples=[10])


class PluginInstallResponseVo(BaseModel):
    """插件安装响应"""

    plugin_id: str = Field(description="插件ID", examples=["author/plugin_name"])
    message: str = Field(description="响应消息", examples=["插件安装成功"])
    status: str = Field(description="插件状态", examples=["installed"])


class PluginOperationResponseVo(BaseModel):
    """插件操作响应（启动、停止等）"""

    plugin_id: str = Field(description="插件ID", examples=["author/plugin_name"])
    message: str = Field(description="响应消息", examples=["插件启动成功"])
    status: str = Field(description="插件状态", examples=["running"])
    success: bool = Field(description="操作是否成功", examples=[True])


class PluginInvokeRequest(BaseModel):
    """插件调用请求"""

    parameters: dict[str, Any] = Field(
        description="调用参数", examples=[{"input": "test"}]
    )
    timeout: int = Field(default=120, description="超时时间（秒）", examples=[120])


class PluginInvokeResponseVo(BaseModel):
    """插件调用响应"""

    plugin_id: str = Field(description="插件ID", examples=["author/plugin_name"])
    action: str = Field(description="调用的方法名", examples=["predict"])
    result: dict[str, Any] = Field(
        description="调用结果", examples=[{"output": "result"}]
    )
    success: bool = Field(description="调用是否成功", examples=[True])
    error: str | None = Field(default=None, description="错误信息")
    duration: float | None = Field(
        default=None, description="调用耗时（秒）", examples=[1.5]
    )


# ======================= 扩展：插件凭证（全局多凭证池） =======================


class PluginCredentialVo(BaseModel):
    """插件扩展凭证VO"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="凭证ID")
    plugin_id: str = Field(description="插件ID")
    scope: str = Field(description="作用域: global|personal(预留)")
    name: str = Field(description="凭证名称")
    provider_name: str | None = Field(default=None, description="工具提供者名")
    credentials: dict[str, Any] | None = Field(
        default=None, description="凭证内容（已解密并脱敏，仅详情接口返回）"
    )
    created_at: str | None = Field(default=None, description="创建时间")
    updated_at: str | None = Field(default=None, description="更新时间")
    created_by: str | None = Field(default=None, description="创建人")
    updated_by: str | None = Field(default=None, description="修改人")


class CreatePluginCredential(BaseModel):
    """创建扩展凭证请求"""

    plugin_id: str = Field(description="插件ID")
    name: str = Field(description="凭证名称")
    credentials: dict[str, Any] = Field(description="凭证内容(JSON)")


class UpdatePluginCredential(BaseModel):
    """更新扩展凭证请求"""

    plugin_id: str | None = Field(default=None, description="插件ID（可选，用于校验）")
    name: str | None = Field(default=None, description="凭证名称")
    credentials: dict[str, Any] | None = Field(
        default=None, description="凭证内容(JSON)"
    )


class PluginCredentialsSchemaVo(BaseModel):
    """插件凭证架构Schema"""

    name: str = Field(description="凭证名称")
    label: str | None = Field(default=None, description="凭证显示名称")
    placeholder: str | None = Field(default=None, description="参数占位符")
    type: str | None = Field(default=None, description="凭证类型")
    required: bool = Field(default=False, description="是否必填")
    description: str | None = Field(default=None, description="凭证描述")
    default: str | None = Field(default=None, description="默认值")
    options: list | None = Field(default_factory=list, description="选项值")
    help: str | None = Field(default=None, description="帮助文本")
    url: str | None = Field(default=None, description="相关URL")


# ======================= 响应模型 =======================


class SuccessRespModel(BaseModel):
    """成功响应基类"""

    code: int = Field(default=200, description="状态码")
    msg: str = Field(default="OK", description="状态描述")
    data: Any | None = Field(default=None, description="响应数据")


class GetPluginListSuccessRespModel(SuccessRespModel):
    data: PluginListResponseVo | None = Field(default=None, description="插件列表")


class InstallPluginSuccessRespModel(SuccessRespModel):
    data: PluginInstallResponseVo | None = Field(
        default=None, description="插件安装信息"
    )


class StartPluginSuccessRespModel(SuccessRespModel):
    data: PluginOperationResponseVo | None = Field(
        default=None, description="插件启动信息"
    )


class StopPluginSuccessRespModel(SuccessRespModel):
    data: PluginOperationResponseVo | None = Field(
        default=None, description="插件停止信息"
    )


class UninstallPluginSuccessRespModel(SuccessRespModel):
    data: PluginOperationResponseVo | None = Field(
        default=None, description="插件卸载信息"
    )


class GetPluginInfoSuccessRespModel(SuccessRespModel):
    data: PluginInfoVo | None = Field(default=None, description="插件信息")


class ListPluginCredentialSuccessRespModel(SuccessRespModel):
    data: list[PluginCredentialVo] | None = Field(default=None, description="凭证列表")


class GetPluginCredentialSuccessRespModel(SuccessRespModel):
    data: PluginCredentialVo | None = Field(default=None, description="凭证详情")


class GetPluginCredentialsSchemaSuccessRespModel(SuccessRespModel):
    data: dict | None = Field(default=None, description="响应数据")


class SavePluginCredentialSuccessRespModel(SuccessRespModel):
    data: PluginCredentialVo | None = Field(default=None, description="保存结果")
