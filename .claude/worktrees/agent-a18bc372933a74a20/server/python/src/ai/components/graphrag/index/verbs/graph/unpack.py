"""包含 unpack_graph,_run_unpack,_unpack_nodes 和 _unpack_edges 方法定义的模块."""

from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_iterable, verb

from ai.components.graphrag.index.utils import load_graph

default_copy = ["level"]


@verb(name="unpack_graph")
def unpack_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    column: str,
    type: str,
    copy: list[str] | None = None,
    embeddings_column: str = "embeddings",
    **kwargs,
) -> TableContainer:
    """
    处理unpack_graph。

    Args:
        input (VerbInput): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        column (str): column 参数。
        type (str): type 参数。
        copy (list[str] | None): copy 参数。
        embeddings_column (str): embeddings_column 参数。
        kwargs: kwargs 参数。

    Returns:
        处理结果。
    """
    if copy is None:
        copy = default_copy
    input_df = input.get_input()
    num_total = len(input_df)
    result = []
    copy = [col for col in copy if col in input_df.columns]
    has_embeddings = embeddings_column in input_df.columns

    for _, row in progress_iterable(input_df.iterrows(), callbacks.progress, num_total):
        # merge the original row with the unpacked graph item
        cleaned_row = {col: row[col] for col in copy}
        embeddings = (
            cast("dict[str, list[float]]", row[embeddings_column])
            if has_embeddings
            else {}
        )

        result.extend(
            [
                {**cleaned_row, **graph_id}
                for graph_id in _run_unpack(
                    cast("str | nx.Graph", row[column]),
                    type,
                    embeddings,
                    kwargs,
                )
            ]
        )

    output_df = pd.DataFrame(result)
    return TableContainer(table=output_df)


def _run_unpack(
    graphml_or_graph: str | nx.Graph,
    unpack_type: str,
    embeddings: dict[str, list[float]],
    args: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    执行unpack。

    Args:
        graphml_or_graph (str | nx.Graph): graphml_or_graph 参数。
        unpack_type (str): unpack_type 参数。
        embeddings (dict[str, list[float]]): embeddings 参数。
        args (dict[str, Any]): args 参数。

    Returns:
        处理结果。
    """
    graph = load_graph(graphml_or_graph)
    if unpack_type == "nodes":
        return _unpack_nodes(graph, embeddings, args)
    if unpack_type == "edges":
        return _unpack_edges(graph, args)
    msg = f"Unknown type {unpack_type}"
    raise ValueError(msg)


def _unpack_nodes(
    graph: nx.Graph, embeddings: dict[str, list[float]], _args: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    处理unpack_nodes。

    Args:
        graph (nx.Graph): graph 参数。
        embeddings (dict[str, list[float]]): embeddings 参数。
        _args (dict[str, Any]): _args 参数。

    Returns:
        处理结果。
    """
    return [
        {
            "label": label,
            **(node_data or {}),
            "graph_embedding": embeddings.get(label),
        }
        for label, node_data in graph.nodes(data=True)  # type: ignore
    ]


def _unpack_edges(graph: nx.Graph, _args: dict[str, Any]) -> list[dict[str, Any]]:
    """
    处理unpack_edges。

    Args:
        graph (nx.Graph): graph 参数。
        _args (dict[str, Any]): _args 参数。

    Returns:
        处理结果。
    """
    return [
        {
            "source": source_id,
            "target": target_id,
            **(edge_data or {}),
        }
        for source_id, target_id, edge_data in graph.edges(data=True)  # type: ignore
    ]
