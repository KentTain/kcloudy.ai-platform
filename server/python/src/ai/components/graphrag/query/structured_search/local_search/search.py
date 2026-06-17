"""本地搜索实现。

LocalSearch implementation.
"""

import logging
import time
from typing import Any

import tiktoken
from ai.components.graphrag.query.context_builder.builders import LocalContextBuilder
from ai.components.graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from ai.components.graphrag.query.llm.base import BaseLLM, BaseLLMCallback
from ai.components.graphrag.query.llm.text_utils import num_tokens
from ai.components.graphrag.query.structured_search.base import (
    BaseSearch,
    SearchResult,
)
from ai.components.graphrag.query.structured_search.local_search.system_prompt import (
    LOCAL_SEARCH_SYSTEM_PROMPT,
)

DEFAULT_LLM_PARAMS = {
    "max_tokens": 1500,
    "temperature": 0.0,
}

log = logging.getLogger(__name__)


class LocalSearch(BaseSearch):
    """
    本地搜索模式的搜索编排。

    Search orchestration for local search mode.
    """

    def __init__(
        self,
        llm: BaseLLM,
        context_builder: LocalContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        system_prompt: str = LOCAL_SEARCH_SYSTEM_PROMPT,
        response_type: str = "多段落，markdown格式",
        callbacks: list[BaseLLMCallback] | None = None,
        llm_params: dict[str, Any] = DEFAULT_LLM_PARAMS,
        context_builder_params: dict | None = None,
    ):
        """
        初始化实例。

        Args:
            llm (BaseLLM): llm 参数。
            context_builder (LocalContextBuilder): context_builder 参数。
            token_encoder (tiktoken.Encoding | None): token_encoder 参数。
            system_prompt (str): system_prompt 参数。
            response_type (str): response_type 参数。
            callbacks (list[BaseLLMCallback] | None): callbacks 参数。
            llm_params (dict[str, Any]): llm_params 参数。
            context_builder_params (dict | None): context_builder_params 参数。
        """
        super().__init__(
            llm=llm,
            context_builder=context_builder,
            token_encoder=token_encoder,
            llm_params=llm_params,
            context_builder_params=context_builder_params or {},
        )
        self.system_prompt = system_prompt
        self.callbacks = callbacks
        self.response_type = response_type

    async def asearch(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """
        构建适合单个上下文窗口的本地搜索上下文并生成用户查询的答案。

        Build local search context that fits a single context window and generate answer for the user query.

        参数 Parameters
        ----------
        - query (str): 用户查询。User query
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - SearchResult: 搜索结果。Search result
        """
        start_time = time.time()
        search_prompt = ""

        # 构建上下文 / Build context
        context_text, context_records = self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **kwargs,
            **self.context_builder_params,
        )
        if not context_text:
            log.info(
                "没有任何的上下文信息，则直接返回空: %s. QUERY: %s", start_time, query
            )
            print(f"没有任何的上下文信息，则直接返回空: {start_time}. QUERY: {query}")
            # 没有任何的上下文信息,则直接返回空 / No context information, return empty
            return SearchResult(
                response="无",
                context_data=context_records,
                context_text=context_text,
                completion_time=time.time() - start_time,
                llm_calls=0,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

        log.info("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        try:
            # 格式化搜索提示 / Format search prompt
            search_prompt = self.system_prompt.format(
                context_data=context_text, response_type=self.response_type
            )

            query = f'根据"已知信息"，回答我的问题：{query}'

            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]

            print(f"system: \n{search_prompt}")
            print(f"user:\n{query}")

            # 调用 LLM 生成答案 / Call LLM to generate answer
            response = await self.llm.agenerate(
                messages=search_messages,
                streaming=False,
                callbacks=self.callbacks,
                **self.llm_params,
            )

            return SearchResult(
                response=response,
                context_data=context_records,
                context_text=context_text,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

        except Exception:
            log.exception("Exception in _asearch")
            return SearchResult(
                response="",
                context_data=context_records,
                context_text=context_text,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

    def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """
        同步构建适合单个上下文窗口的本地搜索上下文并生成用户问题的答案。

        Build local search context that fits a single context window and generate answer for the user question.

        参数 Parameters
        ----------
        - query (str): 用户查询。User query
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - SearchResult: 搜索结果。Search result
        """
        start_time = time.time()
        search_prompt = ""
        # 构建上下文 / Build context
        context_text, context_records = self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **kwargs,
            **self.context_builder_params,
        )
        log.info("GENERATE ANSWER: %d. QUERY: %s", start_time, query)
        try:
            # 格式化搜索提示 / Format search prompt
            search_prompt = self.system_prompt.format(
                context_data=context_text, response_type=self.response_type
            )
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]

            # 调用 LLM 生成答案 / Call LLM to generate answer
            response = self.llm.generate(
                messages=search_messages,
                streaming=True,
                callbacks=self.callbacks,
                **self.llm_params,
            )

            return SearchResult(
                response=response,
                context_data=context_records,
                context_text=context_text,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

        except Exception:
            log.exception("Exception in _map_response_single_batch")
            return SearchResult(
                response="",
                context_data=context_records,
                context_text=context_text,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )
