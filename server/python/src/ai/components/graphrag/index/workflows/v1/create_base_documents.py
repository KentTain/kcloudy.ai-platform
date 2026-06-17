"""包含 build_steps 方法定义的模块."""

from datashaper import DEFAULT_INPUT_NAME

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_base_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建文档表。

    ## 依赖项
    * `workflow:create_final_text_units`
    """
    document_attribute_columns = config.get("document_attribute_columns", [])
    return [
        {
            "verb": "unroll",
            "args": {"column": "document_ids"},
            "input": {"source": "workflow:create_final_text_units"},
        },
        {
            "verb": "select",
            "args": {
                # 我们只需要 chunk id 和 document id
                "columns": ["id", "document_ids", "text"]
            },
        },
        {
            "id": "rename_chunk_doc_id",
            "verb": "rename",
            "args": {
                "columns": {
                    "document_ids": "chunk_doc_id",
                    "id": "chunk_id",
                    "text": "chunk_text",
                }
            },
        },
        {
            "verb": "join",
            "args": {
                # 将 chunk 的 doc id 连接到原始文档上
                "on": ["chunk_doc_id", "id"]
            },
            "input": {"source": "rename_chunk_doc_id", "others": [DEFAULT_INPUT_NAME]},
        },
        {
            "id": "docs_with_text_units",
            "verb": "aggregate_override",
            "args": {
                "groupby": ["id"],
                "aggregations": [
                    {
                        "column": "chunk_id",
                        "operation": "array_agg",
                        "to": "text_units",
                    }
                ],
            },
        },
        {
            "verb": "join",
            "args": {
                "on": ["id", "id"],
                "strategy": "right outer",
            },
            "input": {
                "source": "docs_with_text_units",
                "others": [DEFAULT_INPUT_NAME],
            },
        },
        {
            "verb": "rename",
            "args": {"columns": {"text": "raw_content"}},
        },
        *[
            {
                "verb": "convert",
                "args": {
                    "column": column,
                    "to": column,
                    "type": "string",
                },
            }
            for column in document_attribute_columns
        ],
        {
            "verb": "merge_override",
            "enabled": len(document_attribute_columns) > 0,
            "args": {
                "columns": document_attribute_columns,
                "strategy": "json",
                "to": "attributes",
            },
        },
        {"verb": "convert", "args": {"column": "id", "to": "id", "type": "string"}},
    ]
