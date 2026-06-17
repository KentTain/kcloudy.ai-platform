"""包含 embed_graph 和 run_embeddings 方法定义的模块."""

from enum import Enum
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, derive_from_rows, verb

from ai.components.graphrag.index.utils import load_graph
from ai.components.graphrag.index.verbs.graph.embed.typing import NodeEmbeddings


class EmbedGraphStrategyType(str, Enum):
    """EmbedGraphStrategyType 类定义."""

    node2vec = "node2vec"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


@verb(name="embed_graph")
async def embed_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    column: str,
    to: str,
    **kwargs,
) -> TableContainer:
    """
    嵌入embed_graph。

    Args:
        input (VerbInput): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        strategy (dict[str, Any]): strategy 参数。
        column (str): column 参数。
        to (str): to 参数。
        kwargs: kwargs 参数。

    Returns:
        处理结果。
    """
    output_df = cast("pd.DataFrame", input.get_input())

    strategy_type = strategy.get("type", EmbedGraphStrategyType.node2vec)
    strategy_args = {**strategy}

    async def run_strategy(row):
        """
        执行strategy。

        Args:
            row: row 参数。

        Returns:
            处理结果。
        """
        return run_embeddings(strategy_type, cast("Any", row[column]), strategy_args)

    results = await derive_from_rows(
        output_df,
        run_strategy,
        callbacks=callbacks,
        num_threads=kwargs.get("num_threads"),
    )
    output_df[to] = list(results)
    return TableContainer(table=output_df)


def run_embeddings(
    strategy: EmbedGraphStrategyType,
    graphml_or_graph: str | nx.Graph,
    args: dict[str, Any],
) -> NodeEmbeddings:
    """运行 embedding 方法定义."""
    graph = load_graph(graphml_or_graph)
    match strategy:
        case EmbedGraphStrategyType.node2vec:
            from .strategies.node_2_vec import run as run_node_2_vec

            return run_node_2_vec(graph, args)
        case _:
            msg = f"Unknown strategy {strategy}"
            raise ValueError(msg)
