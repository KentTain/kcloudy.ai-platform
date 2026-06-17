"""Networkx load_graph工具函数定义."""

import networkx as nx


def load_graph(graphml: str | nx.Graph) -> nx.Graph:
    """从graphml文件或networkx图对象加载图."""
    return nx.parse_graphml(graphml) if isinstance(graphml, str) else graphml
