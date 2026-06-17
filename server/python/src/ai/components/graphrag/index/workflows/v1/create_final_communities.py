"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_final_communities"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建最终的社区表。

    ## 依赖项
    * `workflow:create_base_entity_graph`
    """
    return [
        {
            "id": "graph_nodes",
            "verb": "unpack_graph",
            "args": {
                "column": "clustered_graph",
                "type": "nodes",
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "id": "graph_edges",
            "verb": "unpack_graph",
            "args": {
                "column": "clustered_graph",
                "type": "edges",
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "id": "source_clusters",
            "verb": "join",
            "args": {
                "on": ["label", "source"],
            },
            "input": {"source": "graph_nodes", "others": ["graph_edges"]},
        },
        {
            "id": "target_clusters",
            "verb": "join",
            "args": {
                "on": ["label", "target"],
            },
            "input": {"source": "graph_nodes", "others": ["graph_edges"]},
        },
        {
            "id": "concatenated_clusters",
            "verb": "concat",
            "input": {
                "source": "source_clusters",
                "others": ["target_clusters"],
            },
        },
        {
            "id": "combined_clusters",
            "verb": "filter",
            "args": {
                # level_1 是 join 的左侧
                # level_2 是 join 的右侧
                "column": "level_1",
                "criteria": [
                    {"type": "column", "operator": "equals", "value": "level_2"}
                ],
            },
            "input": {"source": "concatenated_clusters"},
        },
        {
            "id": "cluster_relationships",
            "verb": "aggregate_override",
            "args": {
                "groupby": [
                    "cluster",
                    "level_1",  # level_1 是 join 的左侧
                ],
                "aggregations": [
                    {
                        "column": "id_2",  # 这是从上面 join 步骤得到的边的 id
                        "to": "relationship_ids",
                        "operation": "array_agg_distinct",
                    },
                    {
                        "column": "source_id_1",
                        "to": "text_unit_ids",
                        "operation": "array_agg_distinct",
                    },
                ],
            },
            "input": {"source": "combined_clusters"},
        },
        {
            "id": "all_clusters",
            "verb": "aggregate_override",
            "args": {
                "groupby": ["cluster", "level"],
                "aggregations": [{"column": "cluster", "to": "id", "operation": "any"}],
            },
            "input": {"source": "graph_nodes"},
        },
        {
            "verb": "join",
            "args": {
                "on": ["id", "cluster"],
            },
            "input": {"source": "all_clusters", "others": ["cluster_relationships"]},
        },
        {
            "verb": "filter",
            "args": {
                # level 是 join 的左侧
                # level_1 是 join 的右侧
                "column": "level",
                "criteria": [
                    {"type": "column", "operator": "equals", "value": "level_1"}
                ],
            },
        },
        *create_community_title_wf,
        {
            # TODO: Rodrigo 说 "raw_community" 是临时的
            "verb": "copy",
            "args": {
                "column": "id",
                "to": "raw_community",
            },
        },
        {
            "verb": "select",
            "args": {
                "columns": [
                    "id",
                    "title",
                    "level",
                    "raw_community",
                    "relationship_ids",
                    "text_unit_ids",
                ],
            },
        },
    ]


create_community_title_wf = [
    # 用于字符串连接的技巧:"Community " + id
    {
        "verb": "fill",
        "args": {
            "to": "__temp",
            "value": "Community ",
        },
    },
    {
        "verb": "merge",
        "args": {
            "columns": [
                "__temp",
                "id",
            ],
            "to": "title",
            "strategy": "concat",
            "preserveSource": True,
        },
    },
]
