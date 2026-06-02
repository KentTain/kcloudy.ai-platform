"""
AI 模块 Pydantic 模型

包含 AI 相关的所有请求/响应模型。
"""

from .plugin import (
    CreatePluginCredential,
    GetPluginCredentialsSchemaSuccessRespModel,
    GetPluginCredentialSuccessRespModel,
    GetPluginInfoSuccessRespModel,
    GetPluginListSuccessRespModel,
    InstallPluginSuccessRespModel,
    ListPluginCredentialSuccessRespModel,
    PluginConfig,
    PluginCredentialVo,
    PluginCredentialsSchemaVo,
    PluginInfoVo,
    PluginInstallResponseVo,
    PluginInvokeRequest,
    PluginInvokeResponseVo,
    PluginListResponseVo,
    PluginOperationResponseVo,
    SavePluginCredentialSuccessRespModel,
    StartPluginSuccessRespModel,
    StopPluginSuccessRespModel,
    SuccessRespModel,
    UninstallPluginSuccessRespModel,
    UpdatePluginCredential,
)

__all__ = [
    # 基础响应模型
    "SuccessRespModel",
    # 插件配置
    "PluginConfig",
    # 插件信息
    "PluginInfoVo",
    "PluginListResponseVo",
    "PluginInstallResponseVo",
    "PluginOperationResponseVo",
    "PluginInvokeRequest",
    "PluginInvokeResponseVo",
    # 插件凭证
    "PluginCredentialVo",
    "CreatePluginCredential",
    "UpdatePluginCredential",
    "PluginCredentialsSchemaVo",
    # 响应模型
    "GetPluginListSuccessRespModel",
    "InstallPluginSuccessRespModel",
    "StartPluginSuccessRespModel",
    "StopPluginSuccessRespModel",
    "UninstallPluginSuccessRespModel",
    "GetPluginInfoSuccessRespModel",
    "ListPluginCredentialSuccessRespModel",
    "GetPluginCredentialSuccessRespModel",
    "GetPluginCredentialsSchemaSuccessRespModel",
    "SavePluginCredentialSuccessRespModel",
]
