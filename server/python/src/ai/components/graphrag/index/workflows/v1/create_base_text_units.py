"""包含 build_steps 方法定义的模块."""

from datashaper import DEFAULT_INPUT_NAME

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_base_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建文本单元的基础表。

    ## 依赖项
    无
    """
    chunk_column_name = config.get("chunk_column", "chunk")
    chunk_by_columns = config.get("chunk_by", []) or []
    n_tokens_column_name = config.get("n_tokens_column", "n_tokens")
    return [
        {
            "verb": "orderby",
            "args": {
                "orders": [
                    # 排序以确保可重现性
                    {"column": "id", "direction": "asc"},
                ]
            },
            "input": {"source": DEFAULT_INPUT_NAME},
        },
        {
            "verb": "zip",
            "args": {
                # 将文档 id 与文本打包
                # 这样当我们解包 chunks 时,可以恢复文档 id
                "columns": ["id", "text"],
                "to": "text_with_ids",
            },
        },
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": [*chunk_by_columns] if len(chunk_by_columns) > 0 else None,
                "aggregations": [
                    {
                        "column": "text_with_ids",
                        "operation": "array_agg",
                        "to": "texts",
                    }
                ],
            },
        },
        {
            "verb": "chunk",
            "args": {"column": "texts", "to": "chunks", **config.get("text_chunk", {})},
        },
        {
            "verb": "select",
            "args": {
                "columns": [*chunk_by_columns, "chunks"],
            },
        },
        {
            "verb": "unroll",
            "args": {
                "column": "chunks",
            },
        },
        {
            "verb": "rename",
            "args": {
                "columns": {
                    "chunks": chunk_column_name,
                }
            },
        },
        {
            "verb": "genid",
            "args": {
                # 为每个 chunk 生成唯一 id
                "to": "chunk_id",
                "method": "md5_hash",
                "hash": [chunk_column_name],
            },
        },
        {
            "verb": "unzip",
            "args": {
                "column": chunk_column_name,
                "to": ["document_ids", chunk_column_name, n_tokens_column_name],
            },
        },
        {"verb": "copy", "args": {"column": "chunk_id", "to": "id"}},
        {
            # 消除空 chunks
            "verb": "filter",
            "args": {
                "column": chunk_column_name,
                "criteria": [
                    {
                        "type": "value",
                        "operator": "is not empty",
                    }
                ],
            },
        },
    ]
