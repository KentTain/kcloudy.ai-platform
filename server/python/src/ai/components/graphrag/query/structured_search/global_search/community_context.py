"""包含为全局搜索提示构建上下文数据的算法。

Contains algorithms to build context data for global search prompt.
"""

from typing import Any

import pandas as pd
import tiktoken

from ai.components.graphrag.model import CommunityReport, Entity
from ai.components.graphrag.query.context_builder.community_context import (
    build_community_context,
)
from ai.components.graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from ai.components.graphrag.query.structured_search.base import GlobalContextBuilder


class GlobalCommunityContext(GlobalContextBuilder):
    """
    全局搜索社区上下文构建器。

    GlobalSearch community context builder.
    """

    def __init__(
        self,
        community_reports: list[CommunityReport],
        entities: list[Entity] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        random_state: int = 86,
    ):
        """
        初始化实例。

        Args:
            community_reports (list[CommunityReport]): community_reports 参数。
            entities (list[Entity] | None): entities 参数。
            token_encoder (tiktoken.Encoding | None): token_encoder 参数。
            random_state (int): random_state 参数。
        """
        self.community_reports = community_reports
        self.entities = entities
        self.token_encoder = token_encoder
        self.random_state = random_state

    def build_context(
        self,
        conversation_history: ConversationHistory | None = None,
        use_community_summary: bool = True,
        column_delimiter: str = "|",
        shuffle_data: bool = True,
        include_community_rank: bool = False,
        min_community_rank: int = 0,
        community_rank_name: str = "rank",
        include_community_weight: bool = True,
        community_weight_name: str = "occurrence",
        normalize_community_weight: bool = True,
        max_tokens: int = 8000,
        context_name: str = "Reports",
        conversation_history_user_turns_only: bool = True,
        conversation_history_max_turns: int | None = 5,
        **kwargs: Any,
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """
        准备社区报告数据表批次作为全局搜索的上下文数据。

        Prepare batches of community report data table as context data for global search.

        参数 Parameters
        ----------
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - use_community_summary (bool): 是否使用社区摘要。Whether to use community summary
        - column_delimiter (str): 列分隔符。Column delimiter
        - shuffle_data (bool): 是否打乱数据。Whether to shuffle data
        - include_community_rank (bool): 是否包含社区排名。Whether to include community rank
        - min_community_rank (int): 最小社区排名。Minimum community rank
        - community_rank_name (str): 社区排名名称。Community rank name
        - include_community_weight (bool): 是否包含社区权重。Whether to include community weight
        - community_weight_name (str): 社区权重名称。Community weight name
        - normalize_community_weight (bool): 是否归一化社区权重。Whether to normalize community weight
        - max_tokens (int): 最大令牌数。Maximum tokens
        - context_name (str): 上下文名称。Context name
        - conversation_history_user_turns_only (bool): 是否仅包含用户轮次。Whether to include user turns only
        - conversation_history_max_turns (int | None): 对话历史最大轮次。Maximum conversation history turns
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - tuple[str | list[str], dict[str, pd.DataFrame]]: (上下文文本, 上下文数据)。(Context text, context data)
        """
        conversation_history_context = ""
        final_context_data = {}
        if conversation_history:
            # 构建对话历史上下文 / build conversation history context
            (
                conversation_history_context,
                conversation_history_context_data,
            ) = conversation_history.build_context(
                include_user_turns_only=conversation_history_user_turns_only,
                max_qa_turns=conversation_history_max_turns,
                column_delimiter=column_delimiter,
                max_tokens=max_tokens,
                recency_bias=False,
            )
            if conversation_history_context != "":
                final_context_data = conversation_history_context_data

        # 构建社区上下文 / Build community context
        community_context, community_context_data = build_community_context(
            community_reports=self.community_reports,
            entities=self.entities,
            token_encoder=self.token_encoder,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            shuffle_data=shuffle_data,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            community_rank_name=community_rank_name,
            include_community_weight=include_community_weight,
            community_weight_name=community_weight_name,
            normalize_community_weight=normalize_community_weight,
            max_tokens=max_tokens,
            single_batch=False,
            context_name=context_name,
            random_state=self.random_state,
        )
        # 合并对话历史上下文和社区上下文 / Merge conversation history context and community context
        if isinstance(community_context, list):
            final_context = [
                f"{conversation_history_context}\n\n{context}"
                for context in community_context
            ]
        else:
            final_context = f"{conversation_history_context}\n\n{community_context}"

        final_context_data.update(community_context_data)
        return (final_context, final_context_data)
