"""全局和本地上下文构建器的基类。

Base classes for global and local context builders.
"""

from abc import ABC, abstractmethod

import pandas as pd

from ai.components.graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)


class GlobalContextBuilder(ABC):
    """
    全局搜索上下文构建器的基类。

    Base class for global-search context builders.
    """

    @abstractmethod
    def build_context(
        self, conversation_history: ConversationHistory | None = None, **kwargs
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """
        构建全局搜索模式的上下文。

        Build the context for the global search mode.

        参数 Parameters
        ----------
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - **kwargs: 其他参数。Additional parameters

        返回 Returns
        -------
        - tuple[str | list[str], dict[str, pd.DataFrame]]: 上下文文本和数据表。Context text and data tables
        """


class LocalContextBuilder(ABC):
    """
    本地搜索上下文构建器的基类。

    Base class for local-search context builders.
    """

    @abstractmethod
    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """
        构建本地搜索模式的上下文。

        Build the context for the local search mode.

        参数 Parameters
        ----------
        - query (str): 查询字符串。Query string
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - **kwargs: 其他参数。Additional parameters

        返回 Returns
        -------
        - tuple[str | list[str], dict[str, pd.DataFrame]]: 上下文文本和数据表。Context text and data tables
        """
