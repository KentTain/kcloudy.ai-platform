import logging
from abc import abstractmethod
from collections.abc import Generator, Mapping
from typing import Any, Optional, Union, final

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ai_plugin.sdk.entities.agent import AgentInvokeMessage, AgentRuntime
from ai_plugin.sdk.entities.model import AIModelEntity, ModelPropertyKey
from ai_plugin.sdk.entities.model.llm import LLMModelConfig, LLMUsage
from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from ai_plugin.sdk.entities.tool import (
    ToolDescription,
    ToolIdentity,
    ToolParameter,
    ToolProviderType,
)
from ai_plugin.sdk.interfaces.tool import ToolLike, ToolProvider
from ai_plugin.server.core.runtime import Session


class AgentToolIdentity(ToolIdentity):
    """智能体工具标识类

    继承自ToolIdentity，为智能体专用的工具标识。
    """

    provider: str = Field(..., description="工具的提供者")


class AgentModelConfig(LLMModelConfig):
    """智能体模型配置类

    继承自LLMModelConfig，专为智能体设计的模型配置。
    """

    entity: AIModelEntity | None = None
    history_prompt_messages: list[PromptMessage] = Field(default_factory=list)

    @field_validator("history_prompt_messages", mode="before")
    @classmethod
    def convert_prompt_messages(cls, v: list[dict]):
        """转换提示消息为相应的类型

        Args:
            v: 提示消息列表

        Returns:
            转换后的提示消息列表

        Raises:
            ValueError: 当提示消息不是列表格式时抛出异常
        """
        if not isinstance(v, list):
            raise ValueError("提示消息必须是列表格式")

        for i in range(len(v)):
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


class AgentScratchpadUnit(BaseModel):
    """智能体草稿单元实体类

    用于存储智能体思考过程中的临时信息和中间状态。
    """

    class Action(BaseModel):
        """动作实体类

        定义智能体可执行的动作，包括动作名称和动作输入参数。
        """

        action_name: str
        action_input: dict | str

        def to_dict(self) -> dict:
            """转换为字典格式

            Returns:
                包含动作信息的字典
            """
            return {
                "action": self.action_name,
                "action_input": self.action_input,
            }

    agent_response: str | None = ""
    thought: str | None = ""
    action_str: str | None = ""
    observation: str | None = ""
    action: Action | None = None

    def is_final(self) -> bool:
        """检查草稿单元是否为最终状态

        Returns:
            如果是最终状态返回True，否则返回False
        """
        return (
            self.action is not None
            and self.action.action_name.lower() == "final answer"
        )


class ToolInvokeMeta(BaseModel):
    """工具调用元数据类

    存储工具调用的相关元信息，包括耗时、错误信息和工具配置。
    """

    time_cost: float = Field(..., description="工具调用的耗时")
    error: str | None = None
    tool_config: dict | None = None

    @classmethod
    def empty(cls) -> "ToolInvokeMeta":
        """获取空的工具调用元数据实例

        Returns:
            空的ToolInvokeMeta实例
        """
        return cls(time_cost=0.0, error=None, tool_config={})

    @classmethod
    def error_instance(cls, error: str) -> "ToolInvokeMeta":
        """获取包含错误信息的工具调用元数据实例

        Args:
            error: 错误信息

        Returns:
            包含错误的ToolInvokeMeta实例
        """
        return cls(time_cost=0.0, error=error, tool_config={})

    def to_dict(self) -> dict:
        """转换为字典格式

        Returns:
            包含元数据的字典
        """
        return {
            "time_cost": self.time_cost,
            "error": self.error,
            "tool_config": self.tool_config,
        }


class ToolEntity(BaseModel):
    """工具实体类

    定义工具的完整信息，包括标识、参数、描述等。
    """

    identity: AgentToolIdentity
    parameters: list[ToolParameter] = Field(default_factory=list)
    description: ToolDescription | None = None
    output_schema: Mapping[str, Any] | None = None
    has_runtime_parameters: bool = Field(
        default=False, description="工具是否具有运行时参数"
    )
    # 提供者类型
    provider_type: ToolProviderType = ToolProviderType.BUILT_IN

    # 运行时参数
    runtime_parameters: Mapping[str, Any] = {}
    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    @field_validator("parameters", mode="before")
    @classmethod
    def set_parameters(cls, v, validation_info: ValidationInfo) -> list[ToolParameter]:
        """设置参数列表

        Args:
            v: 参数值
            validation_info: 验证信息

        Returns:
            参数列表
        """
        return v or []


class AgentProvider(ToolProvider):
    """智能体提供者类

    为智能体提供工具提供者的实现，智能体总是允许运行。
    """

    def validate_credentials(self, credentials: dict):
        """验证凭证（智能体总是允许运行）

        Args:
            credentials: 凭证字典
        """
        pass

    def _validate_credentials(self, credentials: dict):
        """验证凭证的内部实现（智能体不需要验证）

        Args:
            credentials: 凭证字典
        """
        pass


class AgentStrategy(ToolLike[AgentInvokeMessage]):
    """智能体策略基类

    定义智能体执行策略的抽象基类，提供智能体运行时的核心功能。
    """

    @final
    def __init__(
        self,
        runtime: AgentRuntime,
        session: Session,
    ):
        """初始化智能体策略

        注意：此方法已标记为final，请不要重写

        Args:
            runtime: 智能体运行时环境
            session: 会话对象
        """
        self.runtime = runtime
        self.session = session
        self.response_type = AgentInvokeMessage

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
    def _invoke(self, parameters: dict) -> Generator[AgentInvokeMessage, None, None]:
        """智能体调用的具体实现方法（由子类实现）

        Args:
            parameters: 调用参数

        Returns:
            智能体调用消息生成器
        """
        pass

    ############################################################
    #                    仅供执行器使用                          #
    ############################################################

    def invoke(self, parameters: dict) -> Generator[AgentInvokeMessage, None, None]:
        """调用智能体

        Args:
            parameters: 调用参数

        Returns:
            智能体调用消息生成器
        """
        # 将参数转换为正确的类型
        parameters = self._convert_parameters(parameters)
        return self._invoke(parameters)

    def increase_usage(
        self, final_llm_usage_dict: dict[str, LLMUsage | None], usage: LLMUsage
    ):
        """增加LLM使用量统计

        Args:
            final_llm_usage_dict: 最终LLM使用量字典
            usage: 新增的使用量
        """
        if not final_llm_usage_dict["usage"]:
            final_llm_usage_dict["usage"] = usage
        else:
            llm_usage = final_llm_usage_dict["usage"]
            llm_usage.prompt_tokens += usage.prompt_tokens
            llm_usage.completion_tokens += usage.completion_tokens
            llm_usage.prompt_price += usage.prompt_price
            llm_usage.completion_price += usage.completion_price
            llm_usage.total_price += usage.total_price
            llm_usage.total_tokens += usage.total_tokens

    def recalc_llm_max_tokens(
        self,
        model_entity: AIModelEntity,
        prompt_messages: list[PromptMessage],
        parameters: dict,
    ):
        """重新计算LLM最大token数

        当提示token数 + 最大token数超过模型token限制时，重新计算max_tokens

        Args:
            model_entity: 模型实体
            prompt_messages: 提示消息列表
            parameters: 参数字典
        """
        # 如果sum(prompt_token + max_tokens)超过模型token限制，重新计算max_tokens

        model_context_tokens = model_entity.model_properties.get(
            ModelPropertyKey.CONTEXT_SIZE
        )

        max_tokens = 0
        for parameter_rule in model_entity.parameter_rules:
            if parameter_rule.name == "max_tokens" or (
                parameter_rule.use_template
                and parameter_rule.use_template == "max_tokens"
            ):
                max_tokens = (
                    parameters.get(parameter_rule.name)
                    or parameters.get(parameter_rule.use_template or "")
                ) or 0

        if model_context_tokens is None:
            return -1

        if max_tokens is None:
            max_tokens = 0

        prompt_tokens = self._get_num_tokens_by_gpt2(prompt_messages)

        if prompt_tokens + max_tokens > model_context_tokens:
            max_tokens = max(model_context_tokens - prompt_tokens, 16)

            for parameter_rule in model_entity.parameter_rules:
                if parameter_rule.name == "max_tokens" or (
                    parameter_rule.use_template
                    and parameter_rule.use_template == "max_tokens"
                ):
                    parameters[parameter_rule.name] = max_tokens

    def _get_num_tokens_by_gpt2(self, prompt_messges: list[PromptMessage]) -> int:
        """使用GPT2分词器获取给定提示消息的token数量

        一些提供者模型不提供获取token数量的接口。
        这里使用gpt2分词器来计算token数量。
        此方法可以离线执行，项目中已缓存gpt2分词器。

        Args:
            prompt_messges: 提示消息列表，需要将原始消息转换为纯文本

        Returns:
            token数量
        """
        import tiktoken

        text = " ".join(
            [
                prompt.content
                for prompt in prompt_messges
                if isinstance(prompt.content, str)
            ]
        )
        return len(tiktoken.encoding_for_model("gpt2").encode(text))

    def _init_prompt_tools(
        self, tools: list[ToolEntity] | None
    ) -> list[PromptMessageTool]:
        """初始化工具列表

        Args:
            tools: 工具实体列表

        Returns:
            提示消息工具列表
        """

        prompt_messages_tools = []
        for tool in tools or []:
            try:
                prompt_tool = self._convert_tool_to_prompt_message_tool(tool)
            except Exception:
                # API工具可能已被删除
                logging.exception("转换工具为提示消息工具失败")
                continue

            # 保存提示工具
            prompt_messages_tools.append(prompt_tool)

        return prompt_messages_tools

    def _convert_tool_to_prompt_message_tool(
        self, tool: ToolEntity
    ) -> PromptMessageTool:
        """将工具转换为提示消息工具

        Args:
            tool: 工具实体

        Returns:
            提示消息工具
        """
        message_tool = PromptMessageTool(
            name=tool.identity.name,
            description=tool.description.llm if tool.description else "",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

        parameters = tool.parameters
        for parameter in parameters:
            if parameter.form != ToolParameter.ToolParameterForm.LLM:
                continue

            parameter_type = parameter.type
            if parameter.type in {
                ToolParameter.ToolParameterType.FILE,
                ToolParameter.ToolParameterType.FILES,
            }:
                continue
            if parameter.type in {
                ToolParameter.ToolParameterType.SELECT,
                ToolParameter.ToolParameterType.SECRET_INPUT,
            }:
                parameter_type = ToolParameter.ToolParameterType.STRING
            enum = []
            if parameter.type == ToolParameter.ToolParameterType.SELECT:
                enum = (
                    [option.value for option in parameter.options]
                    if parameter.options
                    else []
                )

            message_tool.parameters["properties"][parameter.name] = {
                "type": parameter_type,
                "description": parameter.llm_description or "",
            }

            if len(enum) > 0:
                message_tool.parameters["properties"][parameter.name]["enum"] = enum

            if parameter.required:
                message_tool.parameters["required"].append(parameter.name)

        return message_tool

    def update_prompt_message_tool(
        self, tool: ToolEntity, prompt_tool: PromptMessageTool
    ) -> PromptMessageTool:
        """更新提示消息工具

        Args:
            tool: 工具实体
            prompt_tool: 提示消息工具

        Returns:
            更新后的提示消息工具
        """
        # 尝试获取工具运行时参数
        tool_runtime_parameters = tool.parameters

        for parameter in tool_runtime_parameters:
            if parameter.form != ToolParameter.ToolParameterForm.LLM:
                continue

            parameter_type = parameter.type
            if parameter.type in {
                ToolParameter.ToolParameterType.FILE,
                ToolParameter.ToolParameterType.FILES,
            }:
                continue
            if parameter.type in {
                ToolParameter.ToolParameterType.SELECT,
                ToolParameter.ToolParameterType.SECRET_INPUT,
            }:
                parameter_type = ToolParameter.ToolParameterType.STRING
            enum = []
            if parameter.type == ToolParameter.ToolParameterType.SELECT:
                enum = (
                    [option.value for option in parameter.options]
                    if parameter.options
                    else []
                )

            prompt_tool.parameters["properties"][parameter.name] = {
                "type": parameter_type,
                "description": parameter.llm_description or "",
            }

            if len(enum) > 0:
                prompt_tool.parameters["properties"][parameter.name]["enum"] = enum

            if (
                parameter.required
                and parameter.name not in prompt_tool.parameters["required"]
            ):
                prompt_tool.parameters["required"].append(parameter.name)

        return prompt_tool
