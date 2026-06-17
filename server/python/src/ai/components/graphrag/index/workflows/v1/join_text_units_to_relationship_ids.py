"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "join_text_units_to_relationship_ids"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建从文本单元 ids 到关系 ids 的连接表。

    ## 依赖项
    * `workflow:create_final_relationships
    """
    return [
        {
            "verb": "select",
            "args": {"columns": ["id", "text_unit_ids"]},
            "input": {"source": "workflow:create_final_relationships"},
        },
        {
            "verb": "unroll",
            "args": {
                "column": "text_unit_ids",
            },
        },
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": ["text_unit_ids"],
                "aggregations": [
                    {
                        "column": "id",
                        "operation": "array_agg_distinct",
                        "to": "relationship_ids",
                    },
                    {
                        "column": "text_unit_ids",
                        "operation": "any",
                        "to": "id",
                    },
                ],
            },
        },
        {
            "id": "text_unit_id_to_relationship_ids",
            "verb": "select",
            "args": {"columns": ["id", "relationship_ids"]},
        },
    ]
