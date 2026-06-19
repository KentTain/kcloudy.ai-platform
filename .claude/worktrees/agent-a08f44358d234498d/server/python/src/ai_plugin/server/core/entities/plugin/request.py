from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)


class PluginInvokeType(StrEnum):
    """插件调用类型枚举"""

    Tool = "tool"  # 工具调用
    Model = "model"  # 模型调用
    Endpoint = "endpoint"  # 端点调用
    Agent = "agent_strategy"  # 代理策略调用
    OAuth = "oauth"  # OAuth调用


class AgentActions(StrEnum):
    """代理操作枚举"""

    InvokeAgentStrategy = "invoke_agent_strategy"  # 调用代理策略


class ToolActions(StrEnum):
    """工具操作枚举"""

    ValidateCredentials = "validate_tool_credentials"  # 验证工具凭证
    InvokeTool = "invoke_tool"  # 调用工具
    GetToolRuntimeParameters = "get_tool_runtime_parameters"  # 获取工具运行时参数


class ModelActions(StrEnum):
    """模型操作枚举"""

    ValidateProviderCredentials = "validate_provider_credentials"  # 验证提供者凭证
    ValidateModelCredentials = "validate_model_credentials"  # 验证模型凭证
    InvokeLLM = "invoke_llm"  # 调用大语言模型
    GetLLMNumTokens = "get_llm_num_tokens"  # 获取LLM令牌数
    InvokeTextEmbedding = "invoke_text_embedding"  # 调用文本嵌入
    GetTextEmbeddingNumTokens = "get_text_embedding_num_tokens"  # 获取文本嵌入令牌数
    InvokeRerank = "invoke_rerank"  # 调用重排序
    InvokeTTS = "invoke_tts"  # 调用文本转语音
    GetTTSVoices = "get_tts_model_voices"  # 获取TTS模型声音
    InvokeSpeech2Text = "invoke_speech2text"  # 调用语音转文本
    InvokeModeration = "invoke_moderation"  # 调用内容审核
    GetAIModelSchemas = "get_ai_model_schemas"  # 获取AI模型架构


class EndpointActions(StrEnum):
    """端点操作枚举"""

    InvokeEndpoint = "invoke_endpoint"  # 调用端点


class OAuthActions(StrEnum):
    """OAuth操作枚举"""

    GetAuthorizationUrl = "get_authorization_url"  # 获取授权URL
    GetCredentials = "get_credentials"  # 获取凭证


# 合并所有访问操作
PluginAccessAction = AgentActions | ToolActions | ModelActions | EndpointActions


class PluginAccessRequest(BaseModel):
    """
    插件访问请求基类

    所有插件访问请求的基础类，包含通用的类型和用户ID字段
    """

    type: PluginInvokeType  # 调用类型
    user_id: str  # 用户ID


class ToolInvokeRequest(PluginAccessRequest):
    """
    工具调用请求

    用于调用指定工具的请求类
    """

    type: PluginInvokeType = PluginInvokeType.Tool  # 调用类型（工具）
    action: ToolActions = ToolActions.InvokeTool  # 操作类型（调用工具）
    provider: str  # 提供者名称
    tool: str  # 工具名称
    credentials: dict  # 凭证信息
    tool_parameters: dict[str, Any]  # 工具参数


class AgentInvokeRequest(PluginAccessRequest):
    """代理调用请求类"""

    type: PluginInvokeType = PluginInvokeType.Agent  # 调用类型（代理）
    action: AgentActions = AgentActions.InvokeAgentStrategy  # 操作类型（调用代理策略）
    agent_strategy_provider: str  # 代理策略提供者
    agent_strategy: str  # 代理策略名称
    agent_strategy_params: dict[str, Any]  # 代理策略参数


class ToolValidateCredentialsRequest(PluginAccessRequest):
    """工具凭证验证请求类"""

    type: PluginInvokeType = PluginInvokeType.Tool  # 调用类型（工具）
    action: ToolActions = ToolActions.ValidateCredentials  # 操作类型（验证凭证）
    provider: str  # 提供者名称
    credentials: dict  # 凭证信息


class ToolGetRuntimeParametersRequest(PluginAccessRequest):
    """获取工具运行时参数请求类"""

    type: PluginInvokeType = PluginInvokeType.Tool  # 调用类型（工具）
    action: ToolActions = (
        ToolActions.GetToolRuntimeParameters
    )  # 操作类型（获取运行时参数）
    provider: str  # 提供者名称
    tool: str  # 工具名称
    credentials: dict  # 凭证信息


class PluginAccessModelRequest(BaseModel):
    """插件访问模型请求基类"""

    type: PluginInvokeType = PluginInvokeType.Model  # 调用类型（模型）
    user_id: str  # 用户ID
    provider: str  # 提供者名称
    model_type: ModelType  # 模型类型
    model: str  # 模型名称
    credentials: dict  # 凭证信息

    model_config = ConfigDict(protected_namespaces=())


class PromptMessageMixin(BaseModel):
    """提示消息混合类"""

    prompt_messages: list[
        UserPromptMessage
        | AssistantPromptMessage
        | SystemPromptMessage
        | ToolPromptMessage
        | PromptMessage
    ]  # 提示消息列表

    # 说明：prompt_messages：原本使用了过于宽泛的基类类型注解 list[PromptMessage]
    # 导致 Pydantic 序列化时只保留基类字段，丢失了子类特有的字段如 tool_call_id
    # 解决方案：
    # 修改类型注解为明确的 Union 类型，支持多态序列化
    # 现在 ToolPromptMessage 的 tool_call_id 字段能正确保留在序列化结果中

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def convert_prompt_messages(cls, v):
        """
        转换提示消息列表

        Args:
            v: 输入的消息数据

        Returns:
            转换后的提示消息列表

        Raises:
            ValueError: 当prompt_messages不是列表时抛出异常
        """
        if not isinstance(v, list):
            raise ValueError("prompt_messages must be a list")

        # 根据角色类型转换为对应的消息对象
        for i in range(len(v)):
            if isinstance(v[i], PromptMessage):
                continue

            if v[i]["role"] == PromptMessageRole.USER.value:
                v[i] = UserPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.ASSISTANT.value:
                v[i] = AssistantPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.SYSTEM.value:
                v[i] = SystemPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.TOOL.value:
                v[i] = ToolPromptMessage(**v[i])
            else:
                v[i] = PromptMessage(**v[i])

        return v


class ModelInvokeLLMRequest(PluginAccessModelRequest, PromptMessageMixin):
    """模型调用LLM请求类"""

    action: ModelActions = ModelActions.InvokeLLM  # 操作类型（调用LLM）

    model_parameters: dict[str, Any]  # 模型参数
    stop: list[str] | None  # 停止词列表
    tools: list[PromptMessageTool] | None  # 工具列表
    stream: bool = True  # 是否流式输出

    model_config = ConfigDict(protected_namespaces=())


class ModelGetLLMNumTokens(PluginAccessModelRequest, PromptMessageMixin):
    """获取LLM令牌数请求类"""

    action: ModelActions = ModelActions.GetLLMNumTokens  # 操作类型（获取LLM令牌数）

    tools: list[PromptMessageTool] | None  # 工具列表


class ModelInvokeTextEmbeddingRequest(PluginAccessModelRequest):
    """模型调用文本嵌入请求类"""

    action: ModelActions = ModelActions.InvokeTextEmbedding  # 操作类型（调用文本嵌入）

    texts: list[str]  # 文本列表


class ModelGetTextEmbeddingNumTokens(PluginAccessModelRequest):
    """获取文本嵌入令牌数请求类"""

    action: ModelActions = (
        ModelActions.GetTextEmbeddingNumTokens
    )  # 操作类型（获取文本嵌入令牌数）

    texts: list[str]  # 文本列表


class ModelInvokeRerankRequest(PluginAccessModelRequest):
    """模型调用重排序请求类"""

    action: ModelActions = ModelActions.InvokeRerank  # 操作类型（调用重排序）

    query: str  # 查询文本
    docs: list[str]  # 文档列表
    score_threshold: float | None  # 分数阈值
    top_n: int | None  # 返回前N个结果


class ModelInvokeTTSRequest(PluginAccessModelRequest):
    """模型调用TTS请求类"""

    action: ModelActions = ModelActions.InvokeTTS  # 操作类型（调用TTS）

    content_text: str  # 要转换的文本内容
    voice: str  # 声音类型
    tenant_id: str  # 租户ID


class ModelGetTTSVoices(PluginAccessModelRequest):
    """获取TTS声音列表请求类"""

    action: ModelActions = ModelActions.GetTTSVoices  # 操作类型（获取TTS声音）

    language: str | None  # 可选的语言


class ModelInvokeSpeech2TextRequest(PluginAccessModelRequest):
    """模型调用语音转文本请求类"""

    action: ModelActions = ModelActions.InvokeSpeech2Text  # 操作类型（调用语音转文本）

    file: str  # 音频文件


class ModelInvokeModerationRequest(PluginAccessModelRequest):
    """模型调用内容审核请求类"""

    action: ModelActions = ModelActions.InvokeModeration  # 操作类型（调用内容审核）

    text: str  # 要审核的文本


class ModelValidateProviderCredentialsRequest(BaseModel):
    """模型验证提供者凭证请求类"""

    type: PluginInvokeType = PluginInvokeType.Model  # 调用类型（模型）
    user_id: str  # 用户ID
    provider: str  # 提供者名称
    credentials: dict  # 凭证信息

    action: ModelActions = (
        ModelActions.ValidateProviderCredentials
    )  # 操作类型（验证提供者凭证）

    model_config = ConfigDict(protected_namespaces=())


class ModelValidateModelCredentialsRequest(BaseModel):
    """模型验证模型凭证请求类"""

    type: PluginInvokeType = PluginInvokeType.Model  # 调用类型（模型）
    user_id: str  # 用户ID
    provider: str  # 提供者名称
    model_type: ModelType  # 模型类型
    model: str  # 模型名称
    credentials: dict  # 凭证信息

    action: ModelActions = (
        ModelActions.ValidateModelCredentials
    )  # 操作类型（验证模型凭证）

    model_config = ConfigDict(protected_namespaces=())


class ModelGetAIModelSchemas(PluginAccessModelRequest):
    """获取AI模型架构请求类"""

    action: ModelActions = ModelActions.GetAIModelSchemas  # 操作类型（获取AI模型架构）


class EndpointInvokeRequest(BaseModel):
    """端点调用请求类"""

    type: PluginInvokeType = PluginInvokeType.Endpoint  # 调用类型（端点）
    action: EndpointActions = EndpointActions.InvokeEndpoint  # 操作类型（调用端点）
    settings: dict  # 设置参数
    raw_http_request: str  # 原始HTTP请求


class OAuthGetAuthorizationUrlRequest(BaseModel):
    """OAuth获取授权URL请求类"""

    type: PluginInvokeType = PluginInvokeType.OAuth  # 调用类型（OAuth）
    action: OAuthActions = OAuthActions.GetAuthorizationUrl  # 操作类型（获取授权URL）
    provider: str  # 提供者名称
    system_credentials: Mapping[str, Any]  # 系统凭证


class OAuthGetCredentialsRequest(BaseModel):
    """OAuth获取凭证请求类"""

    type: PluginInvokeType = PluginInvokeType.OAuth  # 调用类型（OAuth）
    action: OAuthActions = OAuthActions.GetCredentials  # 操作类型（获取凭证）
    provider: str  # 提供者名称
    system_credentials: Mapping[str, Any]  # 系统凭证
    raw_http_request: str  # 原始HTTP请求
