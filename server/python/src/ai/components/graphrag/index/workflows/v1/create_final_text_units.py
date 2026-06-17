"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_final_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建最终的文本单元表。

    ## 依赖项
    * `workflow:create_base_text_units`
    * `workflow:create_final_entities`
    * `workflow:create_final_communities`
    """
    base_text_embed = config.get("text_embed", {})
    text_unit_text_embed_config = config.get("text_unit_text_embed", base_text_embed)
    covariates_enabled = config.get("covariates_enabled", False)
    skip_text_unit_embedding = config.get("skip_text_unit_embedding", False)
    is_using_vector_store = (
        text_unit_text_embed_config.get("strategy", {}).get("vector_store", None)
        is not None
    )

    return [
        {
            "verb": "select",
            "args": {"columns": ["id", "chunk", "document_ids", "n_tokens"]},
            "input": {"source": "workflow:create_base_text_units"},
        },
        {
            "id": "pre_entity_join",
            "verb": "rename",
            "args": {
                "columns": {
                    "chunk": "text",
                },
            },
        },
        # 使用 EntityIDs 扩展 TextUnits
        {
            "id": "pre_relationship_join",
            "verb": "join",
            "args": {
                "on": ["id", "id"],
                "strategy": "left outer",
            },
            "input": {
                "source": "pre_entity_join",
                "others": ["workflow:join_text_units_to_entity_ids"],
            },
        },
        # 使用 RelationshipIDs 扩展 TextUnits
        {
            "id": "pre_covariate_join",
            "verb": "join",
            "args": {
                "on": ["id", "id"],
                "strategy": "left outer",
            },
            "input": {
                "source": "pre_relationship_join",
                "others": ["workflow:join_text_units_to_relationship_ids"],
            },
        },
        # 使用 CovariateIDs 扩展 TextUnits
        {
            "enabled": covariates_enabled,
            "verb": "join",
            "args": {
                "on": ["id", "id"],
                "strategy": "left outer",
            },
            "input": {
                "source": "pre_covariate_join",
                "others": ["workflow:join_text_units_to_covariate_ids"],
            },
        },
        # 将 entities 和 relationships 合并成数组
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": ["id"],  # 来自上面的 join
                "aggregations": [
                    {
                        "column": "text",
                        "operation": "any",
                        "to": "text",
                    },
                    {
                        "column": "n_tokens",
                        "operation": "any",
                        "to": "n_tokens",
                    },
                    {
                        "column": "document_ids",
                        "operation": "any",
                        "to": "document_ids",
                    },
                    {
                        "column": "entity_ids",
                        "operation": "any",
                        "to": "entity_ids",
                    },
                    {
                        "column": "relationship_ids",
                        "operation": "any",
                        "to": "relationship_ids",
                    },
                    *(
                        []
                        if not covariates_enabled
                        else [
                            {
                                "column": "covariate_ids",
                                "operation": "any",
                                "to": "covariate_ids",
                            }
                        ]
                    ),
                ],
            },
        },
        # 最终聚合后进行文本 Embed
        {
            "id": "embedded_text_units",
            "verb": "text_embed",
            "enabled": not skip_text_unit_embedding,
            "args": {
                "column": config.get("column", "text"),
                "to": config.get("to", "text_embedding"),
                **text_unit_text_embed_config,
            },
        },
        {
            "verb": "select",
            "args": {
                # 最终选择以获得正确形状的输出
                "columns": [
                    "id",
                    "text",
                    *(
                        []
                        if (skip_text_unit_embedding or is_using_vector_store)
                        else ["text_embedding"]
                    ),
                    "n_tokens",
                    "document_ids",
                    "entity_ids",
                    "relationship_ids",
                    *([] if not covariates_enabled else ["covariate_ids"]),
                ],
            },
        },
    ]
