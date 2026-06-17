"""包含 'Community' 模型的包。

A package containing the 'Community' model.
"""

from dataclasses import dataclass
from typing import Any

from ai.components.graphrag.model.named import Named


@dataclass
class Community(Named):
    """
    系统中社区的协议。

    社区是通过图聚类算法识别出的实体和关系的集合,
    代表知识图谱中具有相似特征或紧密联系的一组节点。

    A protocol for a community in the system.
    """

    level: str = ""
    """社区层级。

    Community level.
    """

    entity_ids: list[str] | None = None
    """与社区相关的实体 ID 列表(可选)。

    List of entity IDs related to the community (optional).
    """

    relationship_ids: list[str] | None = None
    """与社区相关的关系 ID 列表(可选)。

    List of relationship IDs related to the community (optional).
    """

    covariate_ids: dict[str, list[str]] | None = None
    """与社区相关的不同类型的协变量字典(可选),例如声明(claims)。

    Dictionary of different types of covariates related to the community (optional),
    e.g. claims.
    """

    attributes: dict[str, Any] | None = None
    """与社区关联的其他属性字典(可选)。这些属性将包含在搜索提示词中。

    A dictionary of additional attributes associated with the community (optional).
    To be included in the search prompt.
    """

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        short_id_key: str = "short_id",
        level_key: str = "level",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        covariates_key: str = "covariate_ids",
        attributes_key: str = "attributes",
    ) -> "Community":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            title_key (str): title_key 参数。
            short_id_key (str): short_id_key 参数。
            level_key (str): level_key 参数。
            entities_key (str): entities_key 参数。
            relationships_key (str): relationships_key 参数。
            covariates_key (str): covariates_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return Community(
            id=d[id_key],
            title=d[title_key],
            short_id=d.get(short_id_key),
            level=d[level_key],
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            covariate_ids=d.get(covariates_key),
            attributes=d.get(attributes_key),
        )
