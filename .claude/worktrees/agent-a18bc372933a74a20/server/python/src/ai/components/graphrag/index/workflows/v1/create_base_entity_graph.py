"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_base_entity_graph"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建实体图的基础表。

    ## 依赖项
    * `workflow:create_base_extracted_entities`
    """
    clustering_config = config.get(
        "cluster_graph",
        {"strategy": {"type": "leiden"}},
    )
    embed_graph_config = config.get(
        "embed_graph",
        {
            "strategy": {
                "type": "node2vec",
                "num_walks": config.get("embed_num_walks", 10),
                "walk_length": config.get("embed_walk_length", 40),
                "window_size": config.get("embed_window_size", 2),
                "iterations": config.get("embed_iterations", 3),
                "random_seed": config.get("embed_random_seed", 86),
            }
        },
    )

    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False
    embed_graph_enabled = config.get("embed_graph_enabled", False) or False

    return [
        {
            "verb": "cluster_graph",
            "args": {
                **clustering_config,
                "column": "entity_graph",
                "to": "clustered_graph",
                "level_to": "level",
            },
            "input": ({"source": "workflow:create_summarized_entities"}),
        },
        {
            "verb": "snapshot_rows",
            "enabled": graphml_snapshot_enabled,
            "args": {
                "base_name": "clustered_graph",
                "column": "clustered_graph",
                "formats": [{"format": "text", "extension": "graphml"}],
            },
        },
        {
            "verb": "embed_graph",
            "enabled": embed_graph_enabled,
            "args": {
                "column": "clustered_graph",
                "to": "embeddings",
                **embed_graph_config,
            },
        },
        {
            "verb": "snapshot_rows",
            "enabled": graphml_snapshot_enabled,
            "args": {
                "base_name": "embedded_graph",
                "column": "entity_graph",
                "formats": [{"format": "text", "extension": "graphml"}],
            },
        },
        {
            "verb": "select",
            "args": {
                # 仅为了文档目的而选择,以便我们知道此 workflow 包含什么内容
                "columns": (
                    ["level", "clustered_graph", "embeddings"]
                    if embed_graph_enabled
                    else ["level", "clustered_graph"]
                ),
            },
        },
    ]
