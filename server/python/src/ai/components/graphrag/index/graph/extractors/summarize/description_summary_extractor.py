"""包含'SummarizationResult'和'SummarizeExtractor'模型的模块."""

import json
from dataclasses import dataclass

from ai.components.graphrag.index.graph.extractors.summarize.prompts import (
    SUMMARIZE_PROMPT,
)
from ai.components.graphrag.index.typing import ErrorHandlerFn
from ai.components.graphrag.index.utils.tokens import num_tokens_from_string
from ai.components.graphrag.llm import CompletionLLM

# 输入提示词的最大令牌大小
DEFAULT_MAX_INPUT_TOKENS = 4_000
# LLM回答的最大令牌数
DEFAULT_MAX_SUMMARY_LENGTH = 500


@dataclass
class SummarizationResult:
    """摘要结果类定义."""

    items: str | tuple[str, str]
    description: str


class SummarizeExtractor:
    """摘要提取器类定义."""

    _llm: CompletionLLM
    _entity_name_key: str
    _input_descriptions_key: str
    _summarization_prompt: str
    _on_error: ErrorHandlerFn
    _max_summary_length: int
    _max_input_tokens: int

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        entity_name_key: str | None = None,
        input_descriptions_key: str | None = None,
        summarization_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_summary_length: int | None = None,
        max_input_tokens: int | None = None,
    ):
        """初始化方法定义."""
        # TODO: 简化构造
        self._llm = llm_invoker
        self._entity_name_key = entity_name_key or "entity_name"
        self._input_descriptions_key = input_descriptions_key or "description_list"

        self._summarization_prompt = summarization_prompt or SUMMARIZE_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_summary_length = max_summary_length or DEFAULT_MAX_SUMMARY_LENGTH
        self._max_input_tokens = max_input_tokens or DEFAULT_MAX_INPUT_TOKENS

    async def __call__(
        self,
        items: str | tuple[str, str],
        descriptions: list[str],
    ) -> SummarizationResult:
        """调用方法定义."""
        result = ""
        if len(descriptions) == 0:
            result = ""
        if len(descriptions) == 1:
            result = descriptions[0]
        else:
            result = await self._summarize_descriptions(items, descriptions)

        return SummarizationResult(
            items=items,
            description=result or "",
        )

    async def _summarize_descriptions(
        self, items: str | tuple[str, str], descriptions: list[str]
    ) -> str:
        """将描述汇总为单个描述."""
        sorted_items = sorted(items) if isinstance(items, list) else items

        # 安全检查,应该始终是列表
        if not isinstance(descriptions, list):
            descriptions = [descriptions]

            # 迭代描述,添加所有内容直到达到最大输入令牌数
        usable_tokens = self._max_input_tokens - num_tokens_from_string(
            self._summarization_prompt
        )
        descriptions_collected = []
        result = ""

        for i, description in enumerate(descriptions):
            usable_tokens -= num_tokens_from_string(description)
            descriptions_collected.append(description)

            # 如果缓冲区已满,或所有描述都已添加,则进行汇总
            if (usable_tokens < 0 and len(descriptions_collected) > 1) or (
                i == len(descriptions) - 1
            ):
                # 计算结果(最终或部分)
                result = await self._summarize_descriptions_with_llm(
                    sorted_items, descriptions_collected
                )

                # 如果进行另一轮循环,将值重置为新值
                if i != len(descriptions) - 1:
                    descriptions_collected = [result]
                    usable_tokens = (
                        self._max_input_tokens
                        - num_tokens_from_string(self._summarization_prompt)
                        - num_tokens_from_string(result)
                    )

        return result

    async def _summarize_descriptions_with_llm(
        self, items: str | tuple[str, str] | list[str], descriptions: list[str]
    ):
        """使用LLM汇总描述."""
        response = await self._llm(
            self._summarization_prompt,
            name="summarize",
            variables={
                self._entity_name_key: json.dumps(items, ensure_ascii=False),
                self._input_descriptions_key: json.dumps(
                    sorted(descriptions), ensure_ascii=False
                ),
            },
            model_parameters={"max_tokens": self._max_summary_length},
        )
        # 计算结果
        return str(response.output)
