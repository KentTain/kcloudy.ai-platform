import logging
import re
import time
from abc import abstractmethod
from collections.abc import Generator, Mapping

from pydantic import ConfigDict

from ai_plugin.sdk.entities.model import (
    ModelPropertyKey,
    ModelType,
    ParameterRule,
    ParameterType,
    PriceType,
)
from ai_plugin.sdk.entities.model.llm import (
    LLMMode,
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
    LLMUsage,
)
from ai_plugin.sdk.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageContentType,
    PromptMessageTool,
    SystemPromptMessage,
    UserPromptMessage,
)
from ai_plugin.sdk.interfaces.model.ai_model import AIModel

logger = logging.getLogger(__name__)


class LargeLanguageModel(AIModel):
    """大语言模型类

    提供大语言模型的基本接口和功能实现。
    该类为所有大语言模型提供统一的接口标准，包含调用、token计算等核心功能。
    """

    model_type: ModelType = ModelType.LLM

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> LLMResult | Generator[LLMResultChunk, None, None]:
        """调用大语言模型

        这是一个抽象方法，必须由具体的模型实现类来实现。
        负责与实际的模型API进行交互，发送请求并处理响应。

        Args:
            model: 模型名称，指定要使用的具体模型
            credentials: 模型凭证，包含API密钥等认证信息
            prompt_messages: 提示消息列表，包含用户输入和上下文
            model_parameters: 模型参数，如温度、最大token数等
            tools: 工具调用的工具列表，用于函数调用功能
            stop: 停止词列表，遇到这些词时停止生成
            stream: 是否流式响应，True为流式，False为一次性返回
            user: 唯一用户ID，用于追踪和限制

        Returns:
            完整响应或流式响应块生成器结果

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    @abstractmethod
    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
    ) -> int:
        """获取给定提示消息的token数量

        计算输入消息和工具定义所需的token数量，用于费用计算和限制检查。

        Args:
            model: 模型名称
            credentials: 模型凭证
            prompt_messages: 提示消息列表
            tools: 工具调用的工具列表

        Returns:
            token数量

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    ############################################################
    #                    仅供插件实现使用                        #
    ############################################################

    def enforce_stop_tokens(self, text: str, stop: list[str]) -> str:
        """一旦出现任何停止词就截断文本

        使用正则表达式查找停止词并在首次出现位置截断文本。
        这是一个辅助方法，用于确保模型输出遵循停止词规则。

        Args:
            text: 要处理的文本内容
            stop: 停止词列表

        Returns:
            截断后的文本，去除停止词及其后的内容
        """
        return re.split("|".join(stop), text, maxsplit=1)[0]

    def get_parameter_rules(self, model: str, credentials: dict) -> list[ParameterRule]:
        """获取参数规则

        从模型配置中获取参数验证规则，用于验证输入参数的合法性。

        Args:
            model: 模型名称
            credentials: 模型凭证

        Returns:
            参数规则列表，包含每个参数的类型、范围、默认值等规则
        """
        model_schema = self.get_model_schema(model, credentials)
        if model_schema:
            return model_schema.parameter_rules

        return []

    def get_model_mode(self, model: str, credentials: Mapping | None = None) -> LLMMode:
        """获取模型模式

        确定模型的工作模式，如聊天模式或文本补全模式。

        Args:
            model: 模型名称
            credentials: 模型凭证（可选）

        Returns:
            模型模式，默认为聊天模式
        """
        model_schema = self.get_model_schema(model, credentials)

        mode = LLMMode.CHAT
        if model_schema and model_schema.model_properties.get(ModelPropertyKey.MODE):
            mode = LLMMode.value_of(
                model_schema.model_properties[ModelPropertyKey.MODE]
            )

        return mode

    def _calc_response_usage(
        self,
        model: str,
        credentials: dict,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> LLMUsage:
        """计算响应使用量

        根据输入和输出token数量计算费用和使用统计信息。

        Args:
            model: 模型名称
            credentials: 模型凭证
            prompt_tokens: 提示token数量
            completion_tokens: 完成token数量

        Returns:
            使用量统计信息，包含token数量、价格等详细信息
        """
        # 获取提示价格信息
        prompt_price_info = self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.INPUT,
            tokens=prompt_tokens,
        )

        # 获取完成价格信息
        completion_price_info = self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.OUTPUT,
            tokens=completion_tokens,
        )

        # 构建使用量统计对象
        usage = LLMUsage(
            prompt_tokens=prompt_tokens,
            prompt_unit_price=prompt_price_info.unit_price,
            prompt_price_unit=prompt_price_info.unit,
            prompt_price=prompt_price_info.total_amount,
            completion_tokens=completion_tokens,
            completion_unit_price=completion_price_info.unit_price,
            completion_price_unit=completion_price_info.unit,
            completion_price=completion_price_info.total_amount,
            total_tokens=prompt_tokens + completion_tokens,
            total_price=prompt_price_info.total_amount
            + completion_price_info.total_amount,
            currency=prompt_price_info.currency,
            latency=time.perf_counter() - self.started_at,
        )

        return usage

    def _validate_and_filter_model_parameters(
        self, model: str, model_parameters: dict, credentials: dict
    ) -> dict:
        """验证和过滤模型参数

        根据参数规则验证输入参数，过滤无效参数，设置默认值。
        这是一个关键的参数预处理方法，确保传递给模型的参数都是合法的。

        Args:
            model: 模型名称
            model_parameters: 原始模型参数字典
            credentials: 模型凭证

        Returns:
            验证并过滤后的模型参数字典

        Raises:
            ValueError: 当参数不符合规则时抛出异常
        """
        parameter_rules = self.get_parameter_rules(model, credentials)

        # 验证模型参数
        filtered_model_parameters = {}
        for parameter_rule in parameter_rules:
            parameter_name = parameter_rule.name
            parameter_value = model_parameters.get(parameter_name)

            # 处理参数值为None的情况
            if parameter_value is None:
                if (
                    parameter_rule.use_template
                    and parameter_rule.use_template in model_parameters
                ):
                    # 如果参数值为None，使用模板值变量名替代
                    parameter_value = model_parameters[parameter_rule.use_template]
                else:
                    if parameter_rule.required:
                        if parameter_rule.default is not None:
                            filtered_model_parameters[parameter_name] = (
                                parameter_rule.default
                            )
                            continue
                        else:
                            raise ValueError(f"模型参数 {parameter_name} 是必需的。")
                    else:
                        continue

            # 验证整数类型参数
            if parameter_rule.type == ParameterType.INT:
                if not isinstance(parameter_value, int):
                    raise ValueError(f"模型参数 {parameter_name} 应该是整数类型。")

                # 验证参数值范围
                if (
                    parameter_rule.min is not None
                    and parameter_value < parameter_rule.min
                ):
                    raise ValueError(
                        f"模型参数 {parameter_name} 应该大于或等于 {parameter_rule.min}。"
                    )

                if (
                    parameter_rule.max is not None
                    and parameter_value > parameter_rule.max
                ):
                    raise ValueError(
                        f"模型参数 {parameter_name} 应该小于或等于 {parameter_rule.max}。"
                    )
            # 验证浮点数类型参数
            elif parameter_rule.type == ParameterType.FLOAT:
                if not isinstance(parameter_value, float | int):
                    raise ValueError(f"模型参数 {parameter_name} 应该是浮点数类型。")

                # 验证参数值精度
                if parameter_rule.precision is not None:
                    if parameter_rule.precision == 0:
                        if parameter_value != int(parameter_value):
                            raise ValueError(f"模型参数 {parameter_name} 应该是整数。")
                    else:
                        if parameter_value != round(
                            parameter_value, parameter_rule.precision
                        ):
                            raise ValueError(
                                f"模型参数 {parameter_name} 应该保留到小数点后 {parameter_rule.precision} 位。",
                            )

                # 验证参数值范围
                if (
                    parameter_rule.min is not None
                    and parameter_value < parameter_rule.min
                ):
                    raise ValueError(
                        f"模型参数 {parameter_name} 应该大于或等于 {parameter_rule.min}。"
                    )

                if (
                    parameter_rule.max is not None
                    and parameter_value > parameter_rule.max
                ):
                    raise ValueError(
                        f"模型参数 {parameter_name} 应该小于或等于 {parameter_rule.max}。"
                    )
            # 验证布尔类型参数
            elif parameter_rule.type == ParameterType.BOOLEAN:
                if not isinstance(parameter_value, bool):
                    raise ValueError(f"模型参数 {parameter_name} 应该是布尔类型。")
            # 验证字符串类型参数
            elif parameter_rule.type == ParameterType.STRING:
                if not isinstance(parameter_value, str):
                    raise ValueError(f"模型参数 {parameter_name} 应该是字符串类型。")

                # 验证选项值
                if (
                    parameter_rule.options
                    and parameter_value not in parameter_rule.options
                ):
                    raise ValueError(
                        f"模型参数 {parameter_name} 应该是 {parameter_rule.options} 中的一个。"
                    )
            # 验证文本类型参数
            elif parameter_rule.type == ParameterType.TEXT:
                if not isinstance(parameter_value, str):
                    raise ValueError(f"模型参数 {parameter_name} 应该是字符串类型。")
            else:
                raise ValueError(
                    f"模型参数 {parameter_name} 的类型 {parameter_rule.type} 不被支持。"
                )

            filtered_model_parameters[parameter_name] = parameter_value

        return filtered_model_parameters

    def _code_block_mode_wrapper(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> LLMResult | Generator[LLMResultChunk, None, None]:
        """代码块模式包装器

        确保响应是带有输出markdown引用的代码块格式。
        当需要结构化输出（如JSON、XML）时，使用此包装器来格式化提示和处理响应。

        Args:
            model: 模型名称
            credentials: 模型凭证
            prompt_messages: 提示消息列表
            model_parameters: 模型参数
            tools: 工具调用的工具列表
            stop: 停止词列表
            stream: 是否流式响应
            user: 唯一用户ID

        Returns:
            完整响应或流式响应块生成器结果
        """

        # 代码块提示模板
        block_prompts = """You should always follow the instructions and output a valid {{block}} object.
The structure of the {{block}} object you can found in the instructions, use {"answer": "$your_answer"} as the default structure
if you are not sure about the structure.

<instructions>
{{instructions}}
</instructions>
"""

        code_block = model_parameters.get("response_format", "")
        if not code_block:
            # 如果没有指定响应格式，直接调用原始方法
            return self._invoke(
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters,
                tools=tools,
                stop=stop,
                stream=stream,
                user=user,
            )

        # 移除response_format参数，因为我们将通过提示来控制格式
        model_parameters.pop("response_format")
        stop = stop or []
        # 添加代码块结束标记作为停止词
        stop.extend(["\n```", "```\n"])
        block_prompts = block_prompts.replace("{{block}}", code_block)

        # 检查是否存在系统消息
        if len(prompt_messages) > 0 and isinstance(
            prompt_messages[0], SystemPromptMessage
        ):
            # 覆盖系统消息
            prompt_messages[0] = SystemPromptMessage(
                content=block_prompts.replace(
                    "{{instructions}}", str(prompt_messages[0].content)
                ),
            )
        else:
            # 插入系统消息
            prompt_messages.insert(
                0,
                SystemPromptMessage(
                    content=block_prompts.replace(
                        "{{instructions}}",
                        f"Please output a valid {code_block} object.",
                    ),
                ),
            )

        # 在最后一个用户消息中添加代码块开始标记
        if len(prompt_messages) > 0 and isinstance(
            prompt_messages[-1], UserPromptMessage
        ):
            if isinstance(prompt_messages[-1].content, str):
                prompt_messages[-1].content += f"\n```{code_block}\n"
            elif isinstance(prompt_messages[-1].content, list):
                # 处理多模态内容列表
                for i in range(len(prompt_messages[-1].content) - 1, -1, -1):
                    if (
                        prompt_messages[-1].content[i].type
                        == PromptMessageContentType.TEXT
                    ):
                        prompt_messages[-1].content[i].data += f"\n```{code_block}\n"
                        break
        else:
            # 添加一个用户消息
            prompt_messages.append(UserPromptMessage(content=f"```{code_block}\n"))

        # 调用模型
        response = self._invoke(
            model=model,
            credentials=credentials,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            tools=tools,
            stop=stop,
            stream=stream,
            user=user,
        )

        # 处理流式响应
        if isinstance(response, Generator):
            first_chunk = next(response)

            def new_generator():
                yield first_chunk
                yield from response

            # 根据第一个块的内容选择合适的处理器
            if (
                first_chunk.delta.message.content
                and isinstance(first_chunk.delta.message.content, str)
                and first_chunk.delta.message.content.startswith("`")
            ):
                return self._code_block_mode_stream_processor_with_backtick(
                    model=model,
                    prompt_messages=prompt_messages,
                    input_generator=new_generator(),
                )
            else:
                return self._code_block_mode_stream_processor(
                    model=model,
                    prompt_messages=prompt_messages,
                    input_generator=new_generator(),
                )

        return response

    def _code_block_mode_stream_processor(
        self,
        model: str,
        prompt_messages: list[PromptMessage],
        input_generator: Generator[LLMResultChunk, None, None],
    ) -> Generator[LLMResultChunk, None, None]:
        """代码块模式流处理器

        处理流式响应，确保响应是代码块格式并移除markdown引用标记。
        这个处理器用于解析和清理代码块标记，只保留实际内容。

        Args:
            model: 模型名称
            prompt_messages: 提示消息列表
            input_generator: 输入流生成器

        Yields:
            处理后的响应块，已移除代码块标记
        """
        state = "normal"  # 状态机：normal, in_backticks, skip_content
        backtick_count = 0

        for piece in input_generator:
            if piece.delta.message.content:
                content = piece.delta.message.content
                piece.delta.message.content = ""
                yield piece
                piece = content
            else:
                yield piece
                continue

            new_piece: str = ""
            for char in piece:
                char = str(char)
                if state == "normal":
                    if char == "`":
                        state = "in_backticks"
                        backtick_count = 1
                    else:
                        new_piece += char
                elif state == "in_backticks":
                    if char == "`":
                        backtick_count += 1
                        if backtick_count == 3:
                            state = "skip_content"
                            backtick_count = 0
                    else:
                        new_piece += "`" * backtick_count + char
                        state = "normal"
                        backtick_count = 0
                elif state == "skip_content" and char.isspace():
                    state = "normal"

            if new_piece:
                yield LLMResultChunk(
                    model=model,
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(
                            content=new_piece, tool_calls=[]
                        ),
                    ),
                )

    def _code_block_mode_stream_processor_with_backtick(
        self,
        model: str,
        prompt_messages: list,
        input_generator: Generator[LLMResultChunk, None, None],
    ) -> Generator[LLMResultChunk, None, None]:
        """带反引号的代码块模式流处理器

        处理以反引号开头的流式响应，跳过语言标识符，只提取代码块内容。
        这个版本专门处理以三个反引号开始的代码块响应。

        Args:
            model: 模型名称
            prompt_messages: 提示消息列表
            input_generator: 输入流生成器

        Yields:
            处理后的响应块，只包含代码块内的实际内容
        """
        state = (
            "search_start"  # 状态机：search_start, skip_language, in_code_block, done
        )
        backtick_count = 0

        for piece in input_generator:
            if piece.delta.message.content:
                content = piece.delta.message.content
                # 重置内容以确保我们只处理和产生相关部分
                piece.delta.message.content = ""
                # 在处理之前先产生一个清空内容的块，以维持生成器结构
                yield piece
                piece = content
            else:
                # 直接产生没有内容的块
                yield piece
                continue

            if state == "done":
                continue

            new_piece: str = ""
            for char in piece:
                if state == "search_start":
                    if char == "`":
                        backtick_count += 1
                        if backtick_count == 3:
                            state = "skip_language"
                            backtick_count = 0
                    else:
                        backtick_count = 0
                elif state == "skip_language":
                    # 跳过所有内容直到第一个换行符，标记语言标识符的结束
                    if char == "\n":
                        state = "in_code_block"
                elif state == "in_code_block":
                    if char == "`":
                        backtick_count += 1
                        if backtick_count == 3:
                            state = "done"
                            break
                    else:
                        if backtick_count > 0:
                            # 如果计算了反引号但我们仍在收集内容，那是一个错误的开始
                            new_piece += "`" * backtick_count
                            backtick_count = 0
                        new_piece += str(char)
                elif state == "done":
                    break

            if new_piece:
                # 只产生代码块内收集的内容
                yield LLMResultChunk(
                    model=model,
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(
                            content=new_piece, tool_calls=[]
                        ),
                    ),
                )

    def _wrap_thinking_by_reasoning_content(
        self, delta: dict, is_reasoning: bool
    ) -> tuple[str, bool]:
        """使用推理内容包装思考过程

        如果推理响应来自delta.get("reasoning_content")，我们用HTML思考标签包装它。
        这用于处理具有推理能力的模型的特殊输出格式。

        Args:
            delta: LLM流式响应中的delta字典
            is_reasoning: 是否正在推理状态

        Returns:
            处理后的内容和推理状态的元组
        """
        content = delta.get("content") or ""
        reasoning_content = delta.get("reasoning_content")

        if reasoning_content:
            if not is_reasoning:
                content = "<think>\n" + reasoning_content
                is_reasoning = True
            else:
                content = reasoning_content
        elif is_reasoning and content:
            content = "\n</think>" + content
            is_reasoning = False
        return content, is_reasoning

    ############################################################
    #                 仅供执行器使用                            #
    ############################################################

    def invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict | None = None,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> Generator[LLMResultChunk, None, None]:
        """调用大语言模型

        这是模型调用的主要入口点，负责参数验证、错误处理和响应格式化。
        所有对模型的调用都应该通过这个方法进行。

        Args:
            model: 模型名称
            credentials: 模型凭证
            prompt_messages: 提示消息列表
            model_parameters: 模型参数（可选）
            tools: 工具调用的工具列表（可选）
            stop: 停止词列表（可选）
            stream: 是否流式响应，默认为True
            user: 唯一用户ID（可选）

        Yields:
            LLMResultChunk: 响应块生成器，包含模型输出和元数据

        Raises:
            Exception: 调用过程中的各种异常，经过转换后抛出
        """
        # 验证和过滤模型参数
        if model_parameters is None:
            model_parameters = {}

        model_parameters = self._validate_and_filter_model_parameters(
            model, model_parameters, credentials
        )

        # 记录开始时间，用于计算延迟
        self.started_at = time.perf_counter()

        try:
            # 检查是否需要特殊的响应格式处理
            if "response_format" in model_parameters and model_parameters[
                "response_format"
            ] in {"JSON", "XML"}:
                result = self._code_block_mode_wrapper(
                    model=model,
                    credentials=credentials,
                    prompt_messages=prompt_messages,
                    model_parameters=model_parameters,
                    tools=tools,
                    stop=stop,
                    stream=stream,
                    user=user,
                )
            else:
                # 直接调用实现方法
                result = self._invoke(
                    model,
                    credentials,
                    prompt_messages,
                    model_parameters,
                    tools,
                    stop,
                    stream,
                    user,
                )
        except Exception as e:
            # 转换和重新抛出异常
            raise self._transform_invoke_error(e) from e

        # 处理返回结果
        if isinstance(result, LLMResult):
            # 将完整结果转换为块形式
            yield result.to_llm_result_chunk()
        else:
            # 直接产生流式结果
            yield from result
