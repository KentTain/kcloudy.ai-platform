"""生成图嵌入的工具函数."""

from dataclasses import dataclass

import graspologic as gc
import networkx as nx
import numpy as np


@dataclass
class NodeEmbeddings:
    """节点嵌入类定义."""

    nodes: list[str]
    embeddings: np.ndarray


def embed_nod2vec(
    graph: nx.Graph | nx.DiGraph,
    dimensions: int = 1536,
    num_walks: int = 10,
    walk_length: int = 40,
    window_size: int = 2,
    iterations: int = 3,
    random_seed: int = 86,
) -> NodeEmbeddings:
    """使用Node2Vec生成节点嵌入."""
    # 生成嵌入
    lcc_tensors = gc.embed.node2vec_embed(  # type: ignore
        graph=graph,
        dimensions=dimensions,
        window_size=window_size,
        iterations=iterations,
        num_walks=num_walks,
        walk_length=walk_length,
        random_seed=random_seed,
    )
    return NodeEmbeddings(embeddings=lcc_tensors[0], nodes=lcc_tensors[1])
