"""包含 build_steps 方法定义的模块."""

from datashaper import AsyncType

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_base_extracted_entities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建提取实体的基础表。

    ## 依赖项
    * `workflow:create_base_text_units`
    """
    entity_extraction_config = config.get("entity_extract", {})
    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False
    raw_entity_snapshot_enabled = config.get("raw_entity_snapshot", False) or False

    return [
        {
            "verb": "entity_extract",
            "args": {
                **entity_extraction_config,
                "column": entity_extraction_config.get("text_column", "chunk"),
                "id_column": entity_extraction_config.get("id_column", "chunk_id"),
                "async_mode": entity_extraction_config.get(
                    "async_mode", AsyncType.AsyncIO
                ),
                "to": "entities",
                "graph_to": "entity_graph",
            },
            "input": {"source": "workflow:create_base_text_units"},
        },
        {
            "verb": "snapshot",
            "enabled": raw_entity_snapshot_enabled,
            "args": {
                "name": "raw_extracted_entities",
                "formats": ["json"],
            },
        },
        {
            "verb": "merge_graphs",
            "args": {
                "column": "entity_graph",
                "to": "entity_graph",
                **config.get(
                    "graph_merge_operations",
                    {
                        "nodes": {
                            "source_id": {
                                "operation": "concat",
                                "delimiter": ", ",
                                "distinct": True,
                            },
                            "description": (
                                {
                                    "operation": "concat",
                                    "separator": "\n",
                                    "distinct": False,
                                }
                            ),
                        },
                        "edges": {
                            "source_id": {
                                "operation": "concat",
                                "delimiter": ", ",
                                "distinct": True,
                            },
                            "description": (
                                {
                                    "operation": "concat",
                                    "separator": "\n",
                                    "distinct": False,
                                }
                            ),
                            "weight": "sum",
                        },
                    },
                ),
            },
        },
        {
            "verb": "snapshot_rows",
            "enabled": graphml_snapshot_enabled,
            "args": {
                "base_name": "merged_graph",
                "column": "entity_graph",
                "formats": [{"format": "text", "extension": "graphml"}],
            },
        },
    ]
