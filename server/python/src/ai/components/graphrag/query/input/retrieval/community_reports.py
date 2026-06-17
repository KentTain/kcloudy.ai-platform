"""从社区报告集合中检索数据的工具函数。

Util functions to retrieve community reports from a collection.
"""

from typing import Any, cast

import pandas as pd

from ai.components.graphrag.model import CommunityReport, Entity


def get_candidate_communities(
    selected_entities: list[Entity],
    community_reports: list[CommunityReport],
    include_community_rank: bool = False,
    use_community_summary: bool = False,
) -> pd.DataFrame:
    """
    获取与选定实体相关的所有社区。

    Get all communities that are related to selected entities.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - community_reports (list[CommunityReport]): 社区报告列表。Community reports list
    - include_community_rank (bool): 是否包含社区排名。Whether to include community rank
    - use_community_summary (bool): 是否使用社区摘要而非完整内容。Whether to use community summary instead of full content

    返回 Returns
    -------
    - pd.DataFrame: 包含社区报告数据的数据框。Dataframe containing community report data
    """
    # 从选定的实体中提取所有社区 ID / Extract all community IDs from selected entities
    selected_community_ids = [
        entity.community_ids for entity in selected_entities if entity.community_ids
    ]
    # 展平嵌套列表 / Flatten nested list
    selected_community_ids = [
        item for sublist in selected_community_ids for item in sublist
    ]
    # 根据社区 ID 过滤社区报告 / Filter community reports by community IDs
    selected_reports = [
        community
        for community in community_reports
        if community.id in selected_community_ids
    ]
    return to_community_report_dataframe(
        reports=selected_reports,
        include_community_rank=include_community_rank,
        use_community_summary=use_community_summary,
    )


def to_community_report_dataframe(
    reports: list[CommunityReport],
    include_community_rank: bool = False,
    use_community_summary: bool = False,
) -> pd.DataFrame:
    """
    将社区报告集合转换为 Pandas 数据框。

    Convert a list of communities to a pandas dataframe.

    参数 Parameters
    ----------
    - reports (list[CommunityReport]): 社区报告列表。Community reports list
    - include_community_rank (bool): 是否包含社区排名。Whether to include community rank
    - use_community_summary (bool): 是否使用社区摘要而非完整内容。Whether to use community summary instead of full content

    返回 Returns
    -------
    - pd.DataFrame: 包含社区报告数据的数据框。Dataframe containing community report data
    """
    if len(reports) == 0:
        return pd.DataFrame()

    # 添加表头 / add header
    header = ["id", "title"]
    attribute_cols = list(reports[0].attributes.keys()) if reports[0].attributes else []
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)
    # 根据配置添加摘要或完整内容 / Add summary or content based on configuration
    header.append("summary" if use_community_summary else "content")
    if include_community_rank:
        header.append("rank")

    records = []
    for report in reports:
        new_record = [
            report.short_id if report.short_id else "",
            report.title,
            # 添加所有属性值 / Add all attribute values
            *[
                str(report.attributes.get(field, ""))
                if report.attributes and report.attributes.get(field)
                else ""
                for field in attribute_cols
            ],
        ]
        # 添加内容字段值 / Add content field value
        new_record.append(
            report.summary if use_community_summary else report.full_content
        )
        if include_community_rank:
            new_record.append(str(report.rank))
        records.append(new_record)
    return pd.DataFrame(records, columns=cast("Any", header))
