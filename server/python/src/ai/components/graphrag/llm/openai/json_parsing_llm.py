"""JSON 解析 LLM 装饰器模块。

本模块提供一个 LLM 装饰器,用于自动解析和提取 LLM 响应中的 JSON 内容。
当 LLM 返回的 JSON 字段为空但输出内容不为空时,会尝试解析输出文本为 JSON。
"""

from typing import Unpack

from ai.components.graphrag.llm.openai.utils import try_parse_json_object
from ai.components.graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)


class JsonParsingLLM(LLM[CompletionInput, CompletionOutput]):
    """
    JSON 解析 LLM 装饰器。

    这个装饰器自动尝试解析 LLM 的文本输出为 JSON 对象。
    当请求返回 JSON 格式但解析失败时,会尝试从文本输出中提取和修复 JSON。
    """

    _delegate: CompletionLLM

    def __init__(self, delegate: CompletionLLM):
        """
        初始化实例。

        Args:
            delegate (CompletionLLM): delegate 参数。
        """
        self._delegate = delegate

    async def __call__(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """
        实现 __call__ 协议方法。

        Args:
            input (CompletionInput): input 参数。
            kwargs (Unpack[LLMInput]): kwargs 参数。

        Returns:
            处理结果。
        """
        result = await self._delegate(input, **kwargs)
        # 如果请求了 JSON 输出但 json 字段为空,尝试解析输出文本
        if kwargs.get("json") and result.json is None and result.output is not None:
            _, parsed_json = try_parse_json_object(result.output)
            result.json = parsed_json
        return result
