"""全局搜索实现。

The GlobalSearch Implementation.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
import tiktoken

from ai.components.graphrag.llm.openai.utils import try_parse_json_object
from ai.components.graphrag.query.context_builder.builders import GlobalContextBuilder
from ai.components.graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from ai.components.graphrag.query.llm.base import BaseLLM
from ai.components.graphrag.query.llm.text_utils import num_tokens
from ai.components.graphrag.query.structured_search.base import (
    BaseSearch,
    SearchResult,
)
from ai.components.graphrag.query.structured_search.global_search.callbacks import (
    GlobalSearchLLMCallback,
)
from ai.components.graphrag.query.structured_search.global_search.map_system_prompt import (
    MAP_SYSTEM_PROMPT,
)
from ai.components.graphrag.query.structured_search.global_search.reduce_system_prompt import (
    GENERAL_KNOWLEDGE_INSTRUCTION,
    NO_DATA_ANSWER,
    REDUCE_SYSTEM_PROMPT,
)

DEFAULT_MAP_LLM_PARAMS = {
    "max_tokens": 1000,
    "temperature": 0.0,
}

DEFAULT_REDUCE_LLM_PARAMS = {
    "max_tokens": 2000,
    "temperature": 0.0,
}

log = logging.getLogger(__name__)


@dataclass
class GlobalSearchResult(SearchResult):
    """
    全局搜索结果。

    A GlobalSearch result.
    """

    map_responses: list[SearchResult]
    reduce_context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    reduce_context_text: str | list[str] | dict[str, str]


class GlobalSearch(BaseSearch):
    """
    全局搜索模式的搜索编排。

    Search orchestration for global search mode.
    """

    def __init__(
        self,
        llm: BaseLLM,
        context_builder: GlobalContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        map_system_prompt: str = MAP_SYSTEM_PROMPT,
        reduce_system_prompt: str = REDUCE_SYSTEM_PROMPT,
        response_type: str = "多段落，markdown格式",
        allow_general_knowledge: bool = False,
        general_knowledge_inclusion_prompt: str = GENERAL_KNOWLEDGE_INSTRUCTION,
        json_mode: bool = True,
        callbacks: list[GlobalSearchLLMCallback] | None = None,
        max_data_tokens: int = 8000,
        map_llm_params: dict[str, Any] = DEFAULT_MAP_LLM_PARAMS,
        reduce_llm_params: dict[str, Any] = DEFAULT_REDUCE_LLM_PARAMS,
        context_builder_params: dict[str, Any] | None = None,
        concurrent_coroutines: int = 32,
    ):
        """
        初始化实例。

        Args:
            llm (BaseLLM): llm 参数。
            context_builder (GlobalContextBuilder): context_builder 参数。
            token_encoder (tiktoken.Encoding | None): token_encoder 参数。
            map_system_prompt (str): map_system_prompt 参数。
            reduce_system_prompt (str): reduce_system_prompt 参数。
            response_type (str): response_type 参数。
            allow_general_knowledge (bool): allow_general_knowledge 参数。
            general_knowledge_inclusion_prompt (str): general_knowledge_inclusion_prompt 参数。
            json_mode (bool): json_mode 参数。
            callbacks (list[GlobalSearchLLMCallback] | None): callbacks 参数。
            max_data_tokens (int): max_data_tokens 参数。
            map_llm_params (dict[str, Any]): map_llm_params 参数。
            reduce_llm_params (dict[str, Any]): reduce_llm_params 参数。
            context_builder_params (dict[str, Any] | None): context_builder_params 参数。
            concurrent_coroutines (int): concurrent_coroutines 参数。
        """
        super().__init__(
            llm=llm,
            context_builder=context_builder,
            token_encoder=token_encoder,
            context_builder_params=context_builder_params,
        )
        self.map_system_prompt = map_system_prompt
        self.reduce_system_prompt = reduce_system_prompt
        self.response_type = response_type
        self.allow_general_knowledge = allow_general_knowledge
        self.general_knowledge_inclusion_prompt = general_knowledge_inclusion_prompt
        self.callbacks = callbacks
        self.max_data_tokens = max_data_tokens

        self.map_llm_params = map_llm_params
        self.reduce_llm_params = reduce_llm_params
        if json_mode:
            self.map_llm_params["response_format"] = {"type": "json_object"}
        else:
            # 如果 json_mode 为 False,删除 response_format 键 / remove response_format key if json_mode is False
            self.map_llm_params.pop("response_format", None)

        self.semaphore = asyncio.Semaphore(concurrent_coroutines)

    async def asearch(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs: Any,
    ) -> GlobalSearchResult:
        """
        执行全局搜索。

        全局搜索模式包括两个步骤:
        - 步骤 1: 对社区摘要批次运行并行 LLM 调用,为每个批次生成答案
        - 步骤 2: 合并步骤 1 的答案以生成最终答案

        Perform a global search.

        Global search mode includes two steps:

        - Step 1: Run parallel LLM calls on communities' short summaries to generate answer for each batch
        - Step 2: Combine the answers from step 2 to generate the final answer

        参数 Parameters
        ----------
        - query (str): 用户查询。User query
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - GlobalSearchResult: 全局搜索结果。Global search result
        """
        # 步骤 1: 为每个社区摘要批次生成答案 / Step 1: Generate answers for each batch of community short summaries
        start_time = time.time()
        context_chunks, context_records = self.context_builder.build_context(
            conversation_history=conversation_history, **self.context_builder_params
        )

        if self.callbacks:
            for callback in self.callbacks:
                callback.on_map_response_start(context_chunks)  # type: ignore
        # 并行调用 LLM / Parallel LLM calls
        map_responses = await asyncio.gather(
            *[
                self._map_response_single_batch(
                    context_data=data, query=query, **self.map_llm_params
                )
                for data in context_chunks
            ]
        )
        if self.callbacks:
            for callback in self.callbacks:
                callback.on_map_response_end(map_responses)
        map_llm_calls = sum(response.llm_calls for response in map_responses)
        map_prompt_tokens = sum(response.prompt_tokens for response in map_responses)

        # 步骤 2: 合并步骤 1 的中间答案以生成最终答案 / Step 2: Combine the intermediate answers from step 2 to generate the final answer
        reduce_response = await self._reduce_response(
            map_responses=map_responses,
            query=query,
            **self.reduce_llm_params,
        )

        return GlobalSearchResult(
            response=reduce_response.response,
            context_data=context_records,
            context_text=context_chunks,
            map_responses=map_responses,
            reduce_context_data=reduce_response.context_data,
            reduce_context_text=reduce_response.context_text,
            completion_time=time.time() - start_time,
            llm_calls=map_llm_calls + reduce_response.llm_calls,
            prompt_tokens=map_prompt_tokens + reduce_response.prompt_tokens,
        )

    def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs: Any,
    ) -> GlobalSearchResult:
        """
        同步执行全局搜索。

        Perform a global search synchronously.
        """
        return asyncio.run(self.asearch(query, conversation_history))

    async def _map_response_single_batch(
        self,
        context_data: str,
        query: str,
        **llm_kwargs,
    ) -> SearchResult:
        """
        为单个社区报告块生成答案。

        Generate answer for a single chunk of community reports.

        参数 Parameters
        ----------
        - context_data (str): 社区报告上下文数据。Community report context data
        - query (str): 用户查询。User query
        - **llm_kwargs: LLM 参数。LLM parameters

        返回 Returns
        -------
        - SearchResult: 搜索结果。Search result
        """
        start_time = time.time()
        search_prompt = ""
        try:
            # 格式化搜索提示 / Format search prompt
            search_prompt = self.map_system_prompt.format(context_data=context_data)
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]
            # 使用信号量控制并发 / Use semaphore to control concurrency
            async with self.semaphore:
                search_response = await self.llm.agenerate(
                    messages=search_messages, streaming=False, **llm_kwargs
                )
                log.info("Map response: %s", search_response)
            try:
                # 解析搜索响应 JSON / parse search response json
                processed_response = self.parse_search_response(search_response)
            except ValueError:
                # 清理并重试解析 / Clean up and retry parse
                try:
                    # 解析搜索响应 JSON / parse search response json
                    processed_response = self.parse_search_response(search_response)
                except ValueError:
                    log.warning(
                        "Warning: Error parsing search response json - skipping this batch"
                    )
                    processed_response = []

            return SearchResult(
                response=processed_response,
                context_data=context_data,
                context_text=context_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

        except Exception:
            log.exception("Exception in _map_response_single_batch")
            return SearchResult(
                response=[{"answer": "", "score": 0}],
                context_data=context_data,
                context_text=context_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

    def parse_search_response(self, search_response: str) -> list[dict[str, Any]]:
        """
        解析搜索响应 JSON 并返回关键点列表。

        Parse the search response json and return a list of key points.

        参数 Parameters
        ----------
        - search_response (str): 搜索响应 JSON 字符串。The search response json string

        返回 Returns
        -------
        - list[dict[str, Any]]: 关键点列表,每个关键点是包含 "answer" 和 "score" 键的字典。A list of key points, each key point is a dictionary with "answer" and "score" keys
        """
        search_response, _j = try_parse_json_object(search_response)
        if _j == {}:
            return [{"answer": "", "score": 0}]

        try:
            parsed_elements = json.loads(search_response).get("points")
        except Exception as e:
            log.exception(
                "Error parsing search response json, json=%s", search_response
            )
            raise e

        if not parsed_elements or not isinstance(parsed_elements, list):
            return [{"answer": "", "score": 0}]

        return [
            {
                "answer": element["description"],
                "score": int(element["score"]),
            }
            for element in parsed_elements
            if "description" in element and "score" in element
        ]

    async def _reduce_response(
        self,
        map_responses: list[SearchResult],
        query: str,
        **llm_kwargs,
    ) -> SearchResult:
        """
        将所有单批次的中间响应合并为用户查询的最终答案。

        Combine all intermediate responses from single batches into a final answer to the user query.

        参数 Parameters
        ----------
        - map_responses (list[SearchResult]): Map 阶段的响应列表。List of map responses
        - query (str): 用户查询。User query
        - **llm_kwargs: LLM 参数。LLM parameters

        返回 Returns
        -------
        - SearchResult: 搜索结果。Search result
        """
        text_data = ""
        search_prompt = ""
        start_time = time.time()
        try:
            # 收集所有关键点到单个列表以准备排序 / collect all key points into a single list to prepare for sorting
            key_points = []
            for index, response in enumerate(map_responses):
                if not isinstance(response.response, list):
                    continue
                for element in response.response:
                    if not isinstance(element, dict):
                        continue
                    if "answer" not in element or "score" not in element:
                        continue
                    key_points.append(
                        {
                            "analyst": index,
                            "answer": element["answer"],
                            "score": element["score"],
                        }
                    )

            # 过滤得分为 0 的响应,并按得分降序排列响应 / filter response with score = 0 and rank responses by descending order of score
            filtered_key_points = [
                point
                for point in key_points
                if point["score"] > 0  # type: ignore
            ]

            if len(filtered_key_points) == 0 and not self.allow_general_knowledge:
                # 如果没有找到关键点,返回"我不知道"答案 / return no data answer if no key points are found
                log.warning(
                    "Warning: All map responses have score 0 (i.e., no relevant information found from the dataset), returning a canned 'I do not know' answer. You can try enabling `allow_general_knowledge` to encourage the LLM to incorporate relevant general knowledge, at the risk of increasing hallucinations."
                )
                return SearchResult(
                    response=NO_DATA_ANSWER,
                    context_data="",
                    context_text="",
                    completion_time=time.time() - start_time,
                    llm_calls=0,
                    prompt_tokens=0,
                )

            # 按得分降序排序 / Sort by score in descending order
            filtered_key_points = sorted(
                filtered_key_points,
                key=lambda x: x["score"],  # type: ignore
                reverse=True,  # type: ignore
            )

            # 构建 reduce 阶段的上下文数据 / Build context data for reduce phase
            data = []
            total_tokens = 0
            for point in filtered_key_points:
                formatted_response_data = []
                formatted_response_data.append(
                    f"----Analyst {point['analyst'] + 1}----"
                )
                formatted_response_data.append(
                    f"Importance Score: {point['score']}"  # type: ignore
                )
                formatted_response_data.append(point["answer"])  # type: ignore
                formatted_response_text = "\n".join(formatted_response_data)
                # 检查是否超过最大令牌数 / Check if exceeds max tokens
                if (
                    total_tokens
                    + num_tokens(formatted_response_text, self.token_encoder)
                    > self.max_data_tokens
                ):
                    break
                data.append(formatted_response_text)
                total_tokens += num_tokens(formatted_response_text, self.token_encoder)
            text_data = "\n\n".join(data)

            # 格式化 reduce 提示 / Format reduce prompt
            search_prompt = self.reduce_system_prompt.format(
                report_data=text_data, response_type=self.response_type
            )
            if self.allow_general_knowledge:
                search_prompt += "\n" + self.general_knowledge_inclusion_prompt
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]

            # 调用 LLM 生成最终响应 / Call LLM to generate final response
            search_response = await self.llm.agenerate(
                search_messages,
                streaming=False,
                callbacks=self.callbacks,  # type: ignore
                **llm_kwargs,  # type: ignore
            )
            return SearchResult(
                response=search_response,
                context_data=text_data,
                context_text=text_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )
        except Exception:
            log.exception("Exception in reduce_response")
            return SearchResult(
                response="",
                context_data=text_data,
                context_text=text_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )
