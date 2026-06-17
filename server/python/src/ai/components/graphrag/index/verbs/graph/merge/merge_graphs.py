"""包含 merge_graphs,merge_nodes,merge_edges,merge_attributes,apply_merge_operation 和 _get_detailed_attribute_merge_operation 方法定义的模块."""

from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_iterable, verb

from ai.components.graphrag.index.utils import load_graph
from ai.components.graphrag.index.verbs.graph.merge.defaults import (
    DEFAULT_CONCAT_SEPARATOR,
    DEFAULT_EDGE_OPERATIONS,
    DEFAULT_NODE_OPERATIONS,
)
from ai.components.graphrag.index.verbs.graph.merge.typing import (
    BasicMergeOperation,
    DetailedAttributeMergeOperation,
    NumericOperation,
    StringOperation,
)


@verb(name="merge_graphs")
def merge_graphs(
    input: VerbInput,
    callbacks: VerbCallbacks,
    column: str,
    to: str,
    nodes: dict[str, Any] = DEFAULT_NODE_OPERATIONS,
    edges: dict[str, Any] = DEFAULT_EDGE_OPERATIONS,
    **_kwargs,
) -> TableContainer:
    """
    合并merge_graphs。

    Args:
        input (VerbInput): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        column (str): column 参数。
        to (str): to 参数。
        nodes (dict[str, Any]): nodes 参数。
        edges (dict[str, Any]): edges 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    input_df = input.get_input()
    output = pd.DataFrame()

    node_ops = {
        attrib: _get_detailed_attribute_merge_operation(value)
        for attrib, value in nodes.items()
    }
    edge_ops = {
        attrib: _get_detailed_attribute_merge_operation(value)
        for attrib, value in edges.items()
    }

    mega_graph = nx.Graph()
    num_total = len(input_df)
    for graphml in progress_iterable(input_df[column], callbacks.progress, num_total):
        graph = load_graph(cast("str | nx.Graph", graphml))
        merge_nodes(mega_graph, graph, node_ops)
        merge_edges(mega_graph, graph, edge_ops)

    output[to] = ["\n".join(nx.generate_graphml(mega_graph))]

    return TableContainer(table=output)


def merge_nodes(
    target: nx.Graph,
    subgraph: nx.Graph,
    node_ops: dict[str, DetailedAttributeMergeOperation],
):
    """
    合并merge_nodes。

    Args:
        target (nx.Graph): target 参数。
        subgraph (nx.Graph): subgraph 参数。
        node_ops (dict[str, DetailedAttributeMergeOperation]): node_ops 参数。
    """
    for node in subgraph.nodes:
        if node not in target.nodes:
            target.add_node(node, **(subgraph.nodes[node] or {}))
        else:
            merge_attributes(target.nodes[node], subgraph.nodes[node], node_ops)


def merge_edges(
    target_graph: nx.Graph,
    subgraph: nx.Graph,
    edge_ops: dict[str, DetailedAttributeMergeOperation],
):
    """
    合并merge_edges。

    Args:
        target_graph (nx.Graph): target_graph 参数。
        subgraph (nx.Graph): subgraph 参数。
        edge_ops (dict[str, DetailedAttributeMergeOperation]): edge_ops 参数。
    """
    for source, target, edge_data in subgraph.edges(data=True):  # type: ignore
        if not target_graph.has_edge(source, target):
            target_graph.add_edge(source, target, **(edge_data or {}))
        else:
            merge_attributes(target_graph.edges[(source, target)], edge_data, edge_ops)


def merge_attributes(
    target_item: dict[str, Any] | None,
    source_item: dict[str, Any] | None,
    ops: dict[str, DetailedAttributeMergeOperation],
):
    """
    合并merge_attributes。

    Args:
        target_item (dict[str, Any] | None): target_item 参数。
        source_item (dict[str, Any] | None): source_item 参数。
        ops (dict[str, DetailedAttributeMergeOperation]): ops 参数。
    """
    source_item = source_item or {}
    target_item = target_item or {}
    for op_attrib, op in ops.items():
        if op_attrib == "*":
            for attrib in source_item:
                # If there is a specific handler for this attribute, use it
                # i.e. * provides a default, but you can override it
                if attrib not in ops:
                    apply_merge_operation(target_item, source_item, attrib, op)
        else:
            if op_attrib in source_item or op_attrib in target_item:
                apply_merge_operation(target_item, source_item, op_attrib, op)


def apply_merge_operation(
    target_item: dict[str, Any] | None,
    source_item: dict[str, Any] | None,
    attrib: str,
    op: DetailedAttributeMergeOperation,
):
    """
    处理apply_merge_operation。

    Args:
        target_item (dict[str, Any] | None): target_item 参数。
        source_item (dict[str, Any] | None): source_item 参数。
        attrib (str): attrib 参数。
        op (DetailedAttributeMergeOperation): op 参数。
    """
    source_item = source_item or {}
    target_item = target_item or {}

    if op.operation in (BasicMergeOperation.Replace, StringOperation.Replace):
        target_item[attrib] = source_item.get(attrib, None) or ""
    elif op.operation in (BasicMergeOperation.Skip, StringOperation.Skip):
        target_item[attrib] = target_item.get(attrib, None) or ""
    elif op.operation == StringOperation.Concat:
        separator = op.separator or DEFAULT_CONCAT_SEPARATOR
        target_attrib = target_item.get(attrib, "") or ""
        source_attrib = source_item.get(attrib, "") or ""
        target_item[attrib] = f"{target_attrib}{separator}{source_attrib}"
        if op.distinct:
            # TODO: Slow
            target_item[attrib] = separator.join(
                sorted(set(target_item[attrib].split(separator)))
            )

    # We're assuming that the attribute is numeric
    elif op.operation == NumericOperation.Sum:
        target_item[attrib] = (target_item.get(attrib, 0) or 0) + (
            source_item.get(attrib, 0) or 0
        )
    elif op.operation == NumericOperation.Average:
        target_item[attrib] = (
            (target_item.get(attrib, 0) or 0) + (source_item.get(attrib, 0) or 0)
        ) / 2
    elif op.operation == NumericOperation.Max:
        target_item[attrib] = max(
            (target_item.get(attrib, 0) or 0), (source_item.get(attrib, 0) or 0)
        )
    elif op.operation == NumericOperation.Min:
        target_item[attrib] = min(
            (target_item.get(attrib, 0) or 0), (source_item.get(attrib, 0) or 0)
        )
    elif op.operation == NumericOperation.Multiply:
        target_item[attrib] = (target_item.get(attrib, 1) or 1) * (
            source_item.get(attrib, 1) or 1
        )
    else:
        msg = f"Invalid operation {op.operation}"
        raise ValueError(msg)


def _get_detailed_attribute_merge_operation(
    value: str | dict[str, Any],
) -> DetailedAttributeMergeOperation:
    """
    获取detailed_attribute_merge_operation。

    Args:
        value (str | dict[str, Any]): value 参数。

    Returns:
        处理结果。
    """
    if isinstance(value, str):
        return DetailedAttributeMergeOperation(operation=value)
    return DetailedAttributeMergeOperation(**value)
