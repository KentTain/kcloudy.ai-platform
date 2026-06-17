"""用于生成稳定的最大连通分量的模块,即相同的输入图产生相同的输出最大连通分量."""

from typing import Any, cast

import networkx as nx
from graspologic.utils import largest_connected_component

from ai.components.graphrag.index.graph.utils.normalize_node_names import (
    normalize_node_names,
)


def stable_largest_connected_component(graph: nx.Graph) -> nx.Graph:
    """以稳定的方式返回图的最大连通分量,节点和边已排序."""
    graph = graph.copy()
    graph = cast("nx.Graph", largest_connected_component(graph))
    graph = normalize_node_names(graph)
    return _stabilize_graph(graph)


def _stabilize_graph(graph: nx.Graph) -> nx.Graph:
    """确保具有相同关系的无向图始终以相同的方式读取."""
    fixed_graph = nx.DiGraph() if graph.is_directed() else nx.Graph()

    sorted_nodes = graph.nodes(data=True)
    sorted_nodes = sorted(sorted_nodes, key=lambda x: x[0])

    fixed_graph.add_nodes_from(sorted_nodes)
    edges = list(graph.edges(data=True))

    # 如果图是无向的,我们以稳定的方式创建边,这样我们得到相同的结果
    # 例如:
    # A -> B
    # 在图论中与
    # B -> A
    # 在无向图中是相同的
    # 然而,这可能导致下游问题,因为有时
    # 消费者读取graph.nodes()最终得到[A, B],有时是[B, A]
    # 但它们基于节点的顺序进行某些逻辑判断,所以顺序最终变得很重要
    # 因此我们以稳定的方式对边中的节点进行排序,这样我们总是得到相同的顺序
    if not graph.is_directed():

        def _sort_source_target(edge):
            """
            处理sort_source_target。

            Args:
                edge: edge 参数。

            Returns:
                处理结果。
            """
            source, target, edge_data = edge
            if source > target:
                temp = source
                source = target
                target = temp
            return source, target, edge_data

        edges = [_sort_source_target(edge) for edge in edges]

    def _get_edge_key(source: Any, target: Any) -> str:
        """
        获取edge_key。

        Args:
            source (Any): source 参数。
            target (Any): target 参数。

        Returns:
            处理结果。
        """
        return f"{source} -> {target}"

    edges = sorted(edges, key=lambda x: _get_edge_key(x[0], x[1]))

    fixed_graph.add_edges_from(edges)
    return fixed_graph
