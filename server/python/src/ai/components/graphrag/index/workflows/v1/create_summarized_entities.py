"""包含 build_steps 方法定义的模块."""

from datashaper import AsyncType

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_summarized_entities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建提取实体的基础表。

    ## 依赖项
    * `workflow:create_base_text_units`
    """
    summarize_descriptions_config = config.get("summarize_descriptions", {})
    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False

    return [
        {
            "verb": "summarize_descriptions",
            "args": {
                **summarize_descriptions_config,
                "column": "entity_graph",
                "to": "entity_graph",
                "async_mode": summarize_descriptions_config.get(
                    "async_mode", AsyncType.AsyncIO
                ),
            },
            "input": {"source": "workflow:create_base_extracted_entities"},
        },
        {
            "verb": "snapshot_rows",
            "enabled": graphml_snapshot_enabled,
            "args": {
                "base_name": "summarized_graph",
                "column": "entity_graph",
                "formats": [{"format": "text", "extension": "graphml"}],
            },
        },
    ]
