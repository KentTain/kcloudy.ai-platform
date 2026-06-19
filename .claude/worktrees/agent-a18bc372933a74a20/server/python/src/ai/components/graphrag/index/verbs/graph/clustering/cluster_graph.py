"""包含 cluster_graph,apply_clustering 和 run_layout 方法定义的模块."""

import logging
from enum import Enum
from random import Random
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_iterable, verb

from ai.components.graphrag.index.utils import gen_uuid, load_graph
from ai.components.graphrag.index.verbs.graph.clustering.typing import Communities

log = logging.getLogger(__name__)


@verb(name="cluster_graph")
def cluster_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    column: str,
    to: str,
    level_to: str | None = None,
    **_kwargs,
) -> TableContainer:
    """
    处理cluster_graph。

    Args:
        input (VerbInput): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        strategy (dict[str, Any]): strategy 参数。
        column (str): column 参数。
        to (str): to 参数。
        level_to (str | None): level_to 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    output_df = cast("pd.DataFrame", input.get_input())
    results = output_df[column].apply(lambda graph: run_layout(strategy, graph))

    community_map_to = "communities"
    output_df[community_map_to] = results

    level_to = level_to or f"{to}_level"
    output_df[level_to] = output_df.apply(
        lambda x: list({level for level, _, _ in x[community_map_to]}), axis=1
    )
    output_df[to] = [None] * len(output_df)

    num_total = len(output_df)

    # Go through each of the rows
    graph_level_pairs_column: list[list[tuple[int, str]]] = []
    for _, row in progress_iterable(
        output_df.iterrows(), callbacks.progress, num_total
    ):
        levels = row[level_to]
        graph_level_pairs: list[tuple[int, str]] = []

        # For each of the levels, get the graph and add it to the list
        for level in levels:
            graph = "\n".join(
                nx.generate_graphml(
                    apply_clustering(
                        cast("str", row[column]),
                        cast("Communities", row[community_map_to]),
                        level,
                    )
                )
            )
            graph_level_pairs.append((level, graph))
        graph_level_pairs_column.append(graph_level_pairs)
    output_df[to] = graph_level_pairs_column

    # explode the list of (level, graph) pairs into separate rows
    output_df = output_df.explode(to, ignore_index=True)

    # split the (level, graph) pairs into separate columns
    # TODO: There is probably a better way to do this
    output_df[[level_to, to]] = pd.DataFrame(
        output_df[to].tolist(), index=output_df.index
    )

    # clean up the community map
    output_df.drop(columns=[community_map_to], inplace=True)

    return TableContainer(table=output_df)


# TODO: This should support str | nx.Graph as a graphml param
def apply_clustering(
    graphml: str, communities: Communities, level=0, seed=0xF001
) -> nx.Graph:
    """
    处理apply_clustering。

    Args:
        graphml (str): graphml 参数。
        communities (Communities): communities 参数。
        level: level 参数。
        seed: seed 参数。

    Returns:
        处理结果。
    """
    random = Random(seed)
    graph = nx.parse_graphml(graphml)
    for community_level, community_id, nodes in communities:
        if level == community_level:
            for node in nodes:
                graph.nodes[node]["cluster"] = community_id
                graph.nodes[node]["level"] = level

    # add node degree
    for node_degree in graph.degree:
        graph.nodes[str(node_degree[0])]["degree"] = int(node_degree[1])

    # add node uuid and incremental record id (a human readable id used as reference in the final report)
    for index, node in enumerate(graph.nodes()):
        graph.nodes[node]["human_readable_id"] = index
        graph.nodes[node]["id"] = str(gen_uuid(random))

    # add ids to edges
    for index, edge in enumerate(graph.edges()):
        graph.edges[edge]["id"] = str(gen_uuid(random))
        graph.edges[edge]["human_readable_id"] = index
        graph.edges[edge]["level"] = level
    return graph


class GraphCommunityStrategyType(str, Enum):
    """封装组件图谱检索增强生成中的GraphCommunityStrategyType逻辑。"""

    leiden = "leiden"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


def run_layout(
    strategy: dict[str, Any], graphml_or_graph: str | nx.Graph
) -> Communities:
    """运行布局方法定义."""
    graph = load_graph(graphml_or_graph)
    if len(graph.nodes) == 0:
        log.warning("Graph has no nodes")
        return []

    clusters: dict[int, dict[str, list[str]]] = {}
    strategy_type = strategy.get("type", GraphCommunityStrategyType.leiden)
    match strategy_type:
        case GraphCommunityStrategyType.leiden:
            from .strategies.leiden import run as run_leiden

            clusters = run_leiden(graph, strategy)
        case _:
            msg = f"Unknown clustering strategy {strategy_type}"
            raise ValueError(msg)

    results: Communities = []
    for level in clusters:
        for cluster_id, nodes in clusters[level].items():
            results.append((level, cluster_id, nodes))
    return results
