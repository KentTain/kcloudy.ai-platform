"""全局搜索 LLM 回调。

GlobalSearch LLM Callbacks.
"""

from ai.components.graphrag.query.llm.base import BaseLLMCallback
from ai.components.graphrag.query.structured_search.base import SearchResult


class GlobalSearchLLMCallback(BaseLLMCallback):
    """
    全局搜索 LLM 回调。

    GlobalSearch LLM Callbacks.
    """

    def __init__(self):
        """初始化实例。"""
        super().__init__()
        self.map_response_contexts = []
        self.map_response_outputs = []

    def on_map_response_start(self, map_response_contexts: list[str]):
        """
        处理 map 响应开始时的回调。

        Handle the start of map response.
        """
        self.map_response_contexts = map_response_contexts

    def on_map_response_end(self, map_response_outputs: list[SearchResult]):
        """
        处理 map 响应结束时的回调。

        Handle the end of map response.
        """
        self.map_response_outputs = map_response_outputs
