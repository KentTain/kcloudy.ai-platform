"""包含 build_steps 方法定义的模块."""

from ai.components.graphrag.index.config import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
)

workflow_name = "create_final_community_reports"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    创建最终的社区报告表。

    ## 依���项
    * `workflow:create_base_entity_graph`
    """
    covariates_enabled = config.get("covariates_enabled", False)
    create_community_reports_config = config.get("create_community_reports", {})
    community_report_strategy = create_community_reports_config.get("strategy", {})
    community_report_max_input_length = community_report_strategy.get(
        "max_input_length", 16_000
    )
    base_text_embed = config.get("text_embed", {})
    community_report_full_content_embed_config = config.get(
        "community_report_full_content_embed", base_text_embed
    )
    community_report_summary_embed_config = config.get(
        "community_report_summary_embed", base_text_embed
    )
    community_report_title_embed_config = config.get(
        "community_report_title_embed", base_text_embed
    )
    skip_title_embedding = config.get("skip_title_embedding", False)
    skip_summary_embedding = config.get("skip_summary_embedding", False)
    skip_full_content_embedding = config.get("skip_full_content_embedding", False)

    return [
        #
        # 子workflow:准备节点
        #
        {
            "id": "nodes",
            "verb": "prepare_community_reports_nodes",
            "input": {"source": "workflow:create_final_nodes"},
        },
        #
        # 子workflow:准备边
        #
        {
            "id": "edges",
            "verb": "prepare_community_reports_edges",
            "input": {"source": "workflow:create_final_relationships"},
        },
        #
        # 子workflow:准备声明表
        #
        {
            "id": "claims",
            "enabled": covariates_enabled,
            "verb": "prepare_community_reports_claims",
            "input": {
                "source": "workflow:create_final_covariates",
            }
            if covariates_enabled
            else {},
        },
        #
        # 子workflow:获取社区层次结构
        #
        {
            "id": "community_hierarchy",
            "verb": "restore_community_hierarchy",
            "input": {"source": "nodes"},
        },
        #
        # 主workflow:创建社区报告
        #
        {
            "id": "local_contexts",
            "verb": "prepare_community_reports",
            "args": {"max_tokens": community_report_max_input_length},
            "input": {
                "source": "nodes",
                "nodes": "nodes",
                "edges": "edges",
                **({"claims": "claims"} if covariates_enabled else {}),
            },
        },
        {
            "verb": "create_community_reports",
            "args": {
                **create_community_reports_config,
            },
            "input": {
                "source": "local_contexts",
                "community_hierarchy": "community_hierarchy",
                "nodes": "nodes",
            },
        },
        {
            # 为每个社区报告生成唯一的 ID,与社区 ID 不同
            "verb": "window",
            "args": {"to": "id", "operation": "uuid", "column": "community"},
        },
        {
            "verb": "text_embed",
            "enabled": not skip_full_content_embedding,
            "args": {
                "embedding_name": "community_report_full_content",
                "column": "full_content",
                "to": "full_content_embedding",
                **community_report_full_content_embed_config,
            },
        },
        {
            "verb": "text_embed",
            "enabled": not skip_summary_embedding,
            "args": {
                "embedding_name": "community_report_summary",
                "column": "summary",
                "to": "summary_embedding",
                **community_report_summary_embed_config,
            },
        },
        {
            "verb": "text_embed",
            "enabled": not skip_title_embedding,
            "args": {
                "embedding_name": "community_report_title",
                "column": "title",
                "to": "title_embedding",
                **community_report_title_embed_config,
            },
        },
    ]
