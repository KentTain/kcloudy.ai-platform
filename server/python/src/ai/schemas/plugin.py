"""
插件相关 Pydantic 模型

包含插件配置、插件信息、插件凭证等请求/响应模型。
"""

from datetime import datetime
from typing import Any

from framework.schemas import BaseModel, BasePaginatedQuery
from pydantic import Field


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


class PluginPaginatedListResponseVo(BaseModel):
    """插件分页列表响应"""

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
    data: PluginPaginatedListResponseVo | None = Field(default=None, description="插件列表")


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


class ValidateCredentialRequest(BaseModel):
    """验证凭证请求"""

    credentials: dict[str, Any] = Field(description="待验证的凭证内容(JSON)")


class ValidateCredentialResult(BaseModel):
    """验证凭证结果"""

    success: bool = Field(description="验证是否成功")
    error: str | None = Field(default=None, description="验证失败时的错误信息")


class ValidateCredentialSuccessRespModel(SuccessRespModel):
    data: ValidateCredentialResult | None = Field(default=None, description="验证结果")


# ======================= 运行时管理 =======================


class StartPluginResponse(BaseModel):
    """启动插件响应"""

    plugin_id: str = Field(description="插件ID")
    message: str = Field(description="响应消息")
    status: str = Field(description="插件状态")
    success: bool = Field(description="操作是否成功")
    process_id: int | None = Field(default=None, description="进程ID")
    port: int | None = Field(default=None, description="运行端口")


class StopPluginResponse(BaseModel):
    """停止插件响应"""

    plugin_id: str = Field(description="插件ID")
    message: str = Field(description="响应消息")
    status: str = Field(description="插件状态")
    success: bool = Field(description="操作是否成功")


class PluginConfigResponse(BaseModel):
    """插件配置响应"""

    plugin_id: str = Field(description="插件ID")
    plugin_config: dict[str, Any] | None = Field(default=None, description="插件能力配置")
    runtime_config: dict[str, Any] | None = Field(default=None, description="运行时配置")


class UpdatePluginConfigRequest(BaseModel):
    """更新插件配置请求"""

    runtime_config: dict[str, Any] | None = Field(default=None, description="运行时配置更新")


class RuntimeStateResponse(BaseModel):
    """运行时状态响应"""

    plugin_id: str = Field(description="插件ID")
    status: str = Field(description="运行时状态: active/inactive/frozen")
    process_id: int | None = Field(default=None, description="进程ID")
    port: int | None = Field(default=None, description="运行端口")
    work_directory: str | None = Field(default=None, description="工作目录")
    call_count: int = Field(default=0, description="调用次数")
    error_count: int = Field(default=0, description="错误次数")
    success_rate: float | None = Field(default=None, description="成功率")
    last_started_at: str | None = Field(default=None, description="最后启动时间")
    last_stopped_at: str | None = Field(default=None, description="最后停止时间")
    last_accessed_at: str | None = Field(default=None, description="最后访问时间")
    health_status: str = Field(default="unknown", description="健康状态: healthy/unhealthy/unknown")
    last_error: str | None = Field(default=None, description="最后错误信息")


class RuntimeStateItem(BaseModel):
    """运行时状态摘要项"""

    plugin_id: str = Field(description="插件ID")
    plugin_name: str | None = Field(default=None, description="插件名称")
    status: str = Field(description="运行时状态")
    process_id: int | None = Field(default=None, description="进程ID")
    port: int | None = Field(default=None, description="运行端口")
    memory_mb: float | None = Field(default=None, description="内存占用(MB)")
    cpu_percent: float | None = Field(default=None, description="CPU使用率(%)")


class RuntimeStateListResponse(BaseModel):
    """运行时状态列表响应"""

    items: list[RuntimeStateItem] = Field(default_factory=list, description="运行时状态列表")
    running_count: int = Field(default=0, description="运行中进程数")
    frozen_count: int = Field(default=0, description="冻结进程数")
    total_memory_mb: float = Field(default=0.0, description="总内存占用(MB)")
    total_cpu_percent: float = Field(default=0.0, description="总CPU使用率(%)")


class GetPluginConfigSuccessRespModel(SuccessRespModel):
    data: PluginConfigResponse | None = Field(default=None, description="插件配置响应")


class UpdatePluginConfigSuccessRespModel(SuccessRespModel):
    data: PluginConfigResponse | None = Field(default=None, description="更新插件配置响应")


class GetRuntimeStateSuccessRespModel(SuccessRespModel):
    data: RuntimeStateResponse | None = Field(default=None, description="运行时状态响应")


class GetRuntimeStateListSuccessRespModel(SuccessRespModel):
    data: RuntimeStateListResponse | None = Field(default=None, description="运行时状态列表响应")


# ======================= 统计仪表板 =======================


class PluginStatusStats(BaseModel):
    """插件状态统计"""

    active_count: int = Field(default=0, description="活跃插件数")
    inactive_count: int = Field(default=0, description="停用插件数")
    frozen_count: int = Field(default=0, description="冻结插件数")
    error_count: int = Field(default=0, description="错误插件数")


class PluginUsageStats(BaseModel):
    """插件使用统计"""

    today_invocations: int = Field(default=0, description="今日调用数")
    total_invocations: int = Field(default=0, description="总调用数")
    error_invocations: int = Field(default=0, description="错误调用数")
    success_rate: float = Field(default=0.0, description="成功率")
    avg_response_time_ms: float | None = Field(default=None, description="平均响应时间(ms)")


class PluginRuntimeStats(BaseModel):
    """运行时统计"""

    running_processes: int = Field(default=0, description="运行进程数")
    frozen_processes: int = Field(default=0, description="冻结进程数")
    total_memory_mb: float = Field(default=0.0, description="总内存占用(MB)")
    total_cpu_percent: float = Field(default=0.0, description="总CPU使用率(%)")
    active_endpoints: int = Field(default=0, description="活跃端点数")


class PluginUsageStatisticsResponse(BaseModel):
    """插件使用统计响应"""

    status_stats: PluginStatusStats = Field(description="状态统计")
    usage_stats: PluginUsageStats = Field(description="使用统计")
    runtime_stats: PluginRuntimeStats = Field(description="运行时统计")
    cached_at: str | None = Field(default=None, description="缓存时间")


class GetPluginStatisticsSuccessRespModel(SuccessRespModel):
    data: PluginUsageStatisticsResponse | None = Field(default=None, description="插件统计响应")


# ======================= 可用插件列表（任务 5）=======================


class AvailablePluginQuery(BasePaginatedQuery):
    """可用插件查询请求"""

    type: str | None = Field(default=None, description="插件类型筛选（model/tool/agent）")
    is_recommended: bool | None = Field(default=None, description="是否推荐")


class AvailablePluginVo(BaseModel):
    """可用插件 VO"""

    plugin_id: str = Field(description="插件ID，格式：author/name")
    plugin_unique_identifier: str = Field(description="插件唯一标识符")
    name: str | None = Field(default=None, description="插件名称")
    author: str | None = Field(default=None, description="作者")
    version: str | None = Field(default=None, description="版本号")
    description: str | None = Field(default=None, description="插件描述")
    icon: str | None = Field(default=None, description="图标")
    plugin_type: str | None = Field(default=None, description="插件类型")
    runtime_type: str | None = Field(default=None, description="运行时类型")
    is_installed: bool = Field(default=False, description="是否已安装")
    installation_status: str | None = Field(default=None, description="安装状态：PENDING/ACTIVE/INACTIVE/FAILED")
    is_recommended: bool = Field(default=False, description="是否推荐")
    is_enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")


class AvailablePluginListResponse(BaseModel):
    """可用插件列表响应"""

    items: list[AvailablePluginVo] = Field(default_factory=list, description="可用插件列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")


class GetAvailablePluginsSuccessRespModel(SuccessRespModel):
    data: AvailablePluginListResponse | None = Field(default=None, description="可用插件列表")


# ======================= 安装任务队列（任务 6）=======================


class InstallPluginRequest(BaseModel):
    """安装插件请求"""

    plugin_id: str = Field(description="插件ID")
    auto_start: bool = Field(default=True, description="是否自动启动")


class InstallTaskVo(BaseModel):
    """安装任务 VO"""

    id: str = Field(description="任务ID")
    plugin_id: str = Field(description="插件ID")
    status: str = Field(description="状态：pending/running/completed/failed/timeout")
    progress: int = Field(default=0, description="进度百分比 (0-100)")
    current_step: str | None = Field(default=None, description="当前步骤描述")
    created_at: datetime | None = Field(default=None, description="创建时间")
    started_at: datetime | None = Field(default=None, description="开始时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")


class InstallTaskDetailVo(InstallTaskVo):
    """安装任务详情 VO"""

    plugin_unique_identifier: str | None = Field(default=None, description="插件唯一标识符")
    steps: list[dict[str, Any]] | None = Field(default=None, description="步骤列表")
    error_message: str | None = Field(default=None, description="错误信息")
    logs: list[str] | None = Field(default=None, description="日志列表")


class InstallTaskQuery(BasePaginatedQuery):
    """安装任务查询请求"""

    status: str | None = Field(default=None, description="状态筛选")
    plugin_id: str | None = Field(default=None, description="插件ID筛选")


class InstallTaskListResponse(BaseModel):
    """安装任务列表响应"""

    items: list[InstallTaskVo] = Field(default_factory=list, description="任务列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")


class InstallPluginResponse(BaseModel):
    """安装插件响应"""

    task_id: str = Field(description="任务ID")
    plugin_id: str = Field(description="插件ID")
    message: str = Field(description="响应消息")
    status: str = Field(description="任务状态")


class CreateInstallTaskSuccessRespModel(SuccessRespModel):
    data: InstallPluginResponse | None = Field(default=None, description="创建安装任务响应")


class GetInstallTaskListSuccessRespModel(SuccessRespModel):
    data: InstallTaskListResponse | None = Field(default=None, description="安装任务列表")


class GetInstallTaskDetailSuccessRespModel(SuccessRespModel):
    data: InstallTaskDetailVo | None = Field(default=None, description="安装任务详情")
