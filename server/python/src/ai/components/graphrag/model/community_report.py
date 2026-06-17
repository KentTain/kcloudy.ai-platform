"""包含 'CommunityReport' 模型的包。

A package containing the 'CommunityReport' model.
"""

from dataclasses import dataclass
from typing import Any

from ai.components.graphrag.model.named import Named


@dataclass
class CommunityReport(Named):
    """
    定义由 LLM 生成的社区摘要报告。

    社区报告是对社区的总结性描述,由大语言模型根据社区中的实体,
    关系和其他信息自动生成,用于帮助理解和搜索社区内容。

    Defines an LLM-generated summary report of a community.
    """

    community_id: str
    """此报告关联的社区 ID。

    The ID of the community this report is associated with.
    """

    summary: str = ""
    """报告的摘要。

    Summary of the report.
    """

    full_content: str = ""
    """报告的完整内容。

    Full content of the report.
    """

    rank: float | None = 1.0
    """报告的排名,用于排序(可选)。数值越高表示越重要。

    Rank of the report, used for sorting (optional). Higher means more important.
    """

    summary_embedding: list[float] | None = None
    """报告摘要的语义(文本)嵌入向量(可选)。

    The semantic (i.e. text) embedding of the report summary (optional).
    """

    full_content_embedding: list[float] | None = None
    """报告完整内容的语义(文本)嵌入向量(可选)。

    The semantic (i.e. text) embedding of the full report content (optional).
    """

    attributes: dict[str, Any] | None = None
    """与报告关联的其他属性字典(可选)。

    A dictionary of additional attributes associated with the report (optional).
    """

    custom_add: str | None = None
    """新增标识('true'|'false')"""

    custom_update: str | None = None
    """修改标识('true'|'false')"""

    report_id: str = ""
    """report_id,用于修改"""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        community_id_key: str = "community_id",
        short_id_key: str = "short_id",
        summary_key: str = "summary",
        full_content_key: str = "full_content",
        rank_key: str = "rank",
        summary_embedding_key: str = "summary_embedding",
        full_content_embedding_key: str = "full_content_embedding",
        attributes_key: str = "attributes",
    ) -> "CommunityReport":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            title_key (str): title_key 参数。
            community_id_key (str): community_id_key 参数。
            short_id_key (str): short_id_key 参数。
            summary_key (str): summary_key 参数。
            full_content_key (str): full_content_key 参数。
            rank_key (str): rank_key 参数。
            summary_embedding_key (str): summary_embedding_key 参数。
            full_content_embedding_key (str): full_content_embedding_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return CommunityReport(
            id=d[id_key],
            title=d[title_key],
            community_id=d[community_id_key],
            short_id=d.get(short_id_key),
            summary=d[summary_key],
            full_content=d[full_content_key],
            rank=d[rank_key],
            summary_embedding=d.get(summary_embedding_key),
            full_content_embedding=d.get(full_content_embedding_key),
            attributes=d.get(attributes_key),
        )
