"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_final_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建最终的文档表。

    ## 依赖项
    * `workflow:create_base_documents`
    * `workflow:create_base_document_nodes`
    """
    base_text_embed = config.get("text_embed", {})
    document_raw_content_embed_config = config.get(
        "document_raw_content_embed", base_text_embed
    )
    skip_raw_content_embedding = config.get("skip_raw_content_embedding", False)
    return [
        {
            "verb": "rename",
            "args": {"columns": {"text_units": "text_unit_ids"}},
            "input": {"source": "workflow:create_base_documents"},
        },
        {
            "verb": "text_embed",
            "enabled": not skip_raw_content_embedding,
            "args": {
                "column": "raw_content",
                "to": "raw_content_embedding",
                **document_raw_content_embed_config,
            },
        },
    ]
