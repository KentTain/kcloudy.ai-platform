"""包含社区报告生成实用工具的模块."""

from typing import cast

import pandas as pd

from ai.components.graphrag.index.graph.extractors.community_reports import schemas
from ai.components.graphrag.query.llm.text_utils import num_tokens


def set_context_size(df: pd.DataFrame) -> None:
    """测量上下文中的令牌数量."""
    df[schemas.CONTEXT_SIZE] = df[schemas.CONTEXT_STRING].apply(lambda x: num_tokens(x))


def set_context_exceeds_flag(df: pd.DataFrame, max_tokens: int) -> None:
    """设置一个标志以指示上下文是否超过限制."""
    df[schemas.CONTEXT_EXCEED_FLAG] = df[schemas.CONTEXT_SIZE].apply(
        lambda x: x > max_tokens
    )


def get_levels(df: pd.DataFrame, level_column: str = schemas.NODE_LEVEL) -> list[int]:
    """获取社区的级别."""
    result = sorted(df[level_column].fillna(-1).unique().tolist(), reverse=True)
    return [r for r in result if r != -1]


def filter_nodes_to_level(node_df: pd.DataFrame, level: int) -> pd.DataFrame:
    """将节点过滤到指定级别."""
    return cast("pd.DataFrame", node_df[node_df[schemas.NODE_LEVEL] == level])


def filter_edges_to_nodes(edge_df: pd.DataFrame, nodes: list[str]) -> pd.DataFrame:
    """
    过滤filter_edges_nodes。

    Args:
        edge_df (pd.DataFrame): edge_df 参数。
        nodes (list[str]): nodes 参数。

    Returns:
        处理结果。
    """
    return cast(
        "pd.DataFrame",
        edge_df[
            edge_df[schemas.EDGE_SOURCE].isin(nodes)
            & edge_df[schemas.EDGE_TARGET].isin(nodes)
        ],
    )


def filter_claims_to_nodes(claims_df: pd.DataFrame, nodes: list[str]) -> pd.DataFrame:
    """
    过滤filter_claims_nodes。

    Args:
        claims_df (pd.DataFrame): claims_df 参数。
        nodes (list[str]): nodes 参数。

    Returns:
        处理结果。
    """
    return cast(
        "pd.DataFrame",
        claims_df[claims_df[schemas.CLAIM_SUBJECT].isin(nodes)],
    )
