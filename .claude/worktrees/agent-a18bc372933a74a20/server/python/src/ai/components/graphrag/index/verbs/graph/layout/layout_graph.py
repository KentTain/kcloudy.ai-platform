"""包含 layout_graph,_run_layout 和 _apply_layout_to_graph 方法定义的模块."""

from enum import Enum
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_callback, verb

from ai.components.graphrag.index.graph.visualization import GraphLayout
from ai.components.graphrag.index.utils import load_graph
from ai.components.graphrag.index.verbs.graph.embed.typing import NodeEmbeddings


class LayoutGraphStrategyType(str, Enum):
    """封装组件图谱检索增强生成中的LayoutGraphStrategyType逻辑。"""

    umap = "umap"
    zero = "zero"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


@verb(name="layout_graph")
def layout_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    embeddings_column: str,
    graph_column: str,
    to: str,
    graph_to: str | None = None,
    **_kwargs: dict,
) -> TableContainer:
    """
    处理layout_graph。

    Args:
        input (VerbInput): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        strategy (dict[str, Any]): strategy 参数。
        embeddings_column (str): embeddings_column 参数。
        graph_column (str): graph_column 参数。
        to (str): to 参数。
        graph_to (str | None): graph_to 参数。
        _kwargs (dict): _kwargs 参数。

    Returns:
        处理结果。
    """
    output_df = cast("pd.DataFrame", input.get_input())

    num_items = len(output_df)
    strategy_type = strategy.get("type", LayoutGraphStrategyType.umap)
    strategy_args = {**strategy}

    has_embeddings = embeddings_column in output_df.columns

    layouts = output_df.apply(
        progress_callback(
            lambda row: _run_layout(
                strategy_type,
                row[graph_column],
                row[embeddings_column] if has_embeddings else {},
                strategy_args,
                callbacks,
            ),
            callbacks.progress,
            num_items,
        ),
        axis=1,
    )
    output_df[to] = layouts.apply(lambda layout: [pos.to_pandas() for pos in layout])
    if graph_to is not None:
        output_df[graph_to] = output_df.apply(
            lambda row: _apply_layout_to_graph(
                row[graph_column], cast("GraphLayout", layouts[row.name])
            ),
            axis=1,
        )
    return TableContainer(table=output_df)


def _run_layout(
    strategy: LayoutGraphStrategyType,
    graphml_or_graph: str | nx.Graph,
    embeddings: NodeEmbeddings,
    args: dict[str, Any],
    reporter: VerbCallbacks,
) -> GraphLayout:
    """
    执行layout。

    Args:
        strategy (LayoutGraphStrategyType): strategy 参数。
        graphml_or_graph (str | nx.Graph): graphml_or_graph 参数。
        embeddings (NodeEmbeddings): embeddings 参数。
        args (dict[str, Any]): args 参数。
        reporter (VerbCallbacks): reporter 参数。

    Returns:
        处理结果。
    """
    graph = load_graph(graphml_or_graph)
    match strategy:
        case LayoutGraphStrategyType.umap:
            from .methods.umap import run as run_umap

            return run_umap(
                graph,
                embeddings,
                args,
                lambda e, stack, d: reporter.error("Error in Umap", e, stack, d),
            )
        case LayoutGraphStrategyType.zero:
            from .methods.zero import run as run_zero

            return run_zero(
                graph,
                args,
                lambda e, stack, d: reporter.error("Error in Zero", e, stack, d),
            )
        case _:
            msg = f"Unknown strategy {strategy}"
            raise ValueError(msg)


def _apply_layout_to_graph(
    graphml_or_graph: str | nx.Graph, layout: GraphLayout
) -> str:
    """
    处理apply_layout_graph。

    Args:
        graphml_or_graph (str | nx.Graph): graphml_or_graph 参数。
        layout (GraphLayout): layout 参数。

    Returns:
        处理结果。
    """
    graph = load_graph(graphml_or_graph)
    for node_position in layout:
        if node_position.label in graph.nodes:
            graph.nodes[node_position.label]["x"] = node_position.x
            graph.nodes[node_position.label]["y"] = node_position.y
            graph.nodes[node_position.label]["size"] = node_position.size
    return "\n".join(nx.generate_graphml(graph))
