"""拓扑排序工具方法."""

from graphlib import TopologicalSorter


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """拓扑排序."""
    ts = TopologicalSorter(graph)
    return list(ts.static_order())
