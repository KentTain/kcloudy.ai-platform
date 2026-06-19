"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "join_text_units_to_covariate_ids"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建最终的文本单元表。

    ## 依赖项
    * `workflow:create_final_covariates`
    """
    return [
        {
            "verb": "select",
            "args": {"columns": ["id", "text_unit_id"]},
            "input": {"source": "workflow:create_final_covariates"},
        },
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": ["text_unit_id"],
                "aggregations": [
                    {
                        "column": "id",
                        "operation": "array_agg_distinct",
                        "to": "covariate_ids",
                    },
                    {
                        "column": "text_unit_id",
                        "operation": "any",
                        "to": "id",
                    },
                ],
            },
        },
    ]
