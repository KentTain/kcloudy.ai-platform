"""包含 'Entity' 模型的包。

A package containing the 'Entity' model.
"""

from dataclasses import dataclass
from typing import Any

from ai.components.graphrag.model.named import Named


@dataclass
class Entity(Named):
    """
    系统中实体的协议。

    表示知识图谱中的实体节点,包含实体的基本信息,嵌入向量,关联关系等。

    A protocol for an entity in the system.
    """

    type: str | None = None
    """实体的类型(可以是任意字符串,可选)。

    Type of the entity (can be any string, optional).
    """

    description: str | None = None
    """实体的描述(可选)。

    Description of the entity (optional).
    """

    description_embedding: list[float] | None = None
    """实体描述的语义(文本)嵌入向量(可选)。

    The semantic (i.e. text) embedding of the entity (optional).
    """

    name_embedding: list[float] | None = None
    """实体名称的语义(文本)嵌入向量(可选)。

    The semantic (i.e. text) embedding of the entity (optional).
    """

    graph_embedding: list[float] | None = None
    """实体的图嵌入向量,通常来自 node2vec 算法(可选)。

    The graph embedding of the entity, likely from node2vec (optional).
    """

    community_ids: list[str] | None = None
    """实体所属的社区 ID 列表(可选)。

    The community IDs of the entity (optional).
    """

    text_unit_ids: list[str] | None = None
    """实体出现的文本单元 ID 列表(可选)。

    List of text unit IDs in which the entity appears (optional).
    """

    document_ids: list[str] | None = None
    """实体出现的文档 ID 列表(可选)。

    List of document IDs in which the entity appears (optional).
    """

    rank: int | None = 1
    """实体的排名,用于排序(可选)。较高的排名表示更重要的实体。
    这可以基于中心性或其他指标来确定。

    Rank of the entity, used for sorting (optional). Higher rank indicates more important entity.
    This can be based on centrality or other metrics.
    """

    attributes: dict[str, Any] | None = None
    """与实体关联的其他属性(可选),例如开始时间,结束时间等。
    这些属性将包含在搜索提示词中。

    Additional attributes associated with the entity (optional), e.g. start time, end time, etc.
    To be included in the search prompt.
    """

    custom_add: str | None = None
    """新增标识('true'|'false')"""

    custom_update: str | None = None
    """修改标识('true'|'false')"""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        title_key: str = "title",
        type_key: str = "type",
        description_key: str = "description",
        description_embedding_key: str = "description_embedding",
        name_embedding_key: str = "name_embedding",
        graph_embedding_key: str = "graph_embedding",
        community_key: str = "community",
        text_unit_ids_key: str = "text_unit_ids",
        document_ids_key: str = "document_ids",
        rank_key: str = "degree",
        attributes_key: str = "attributes",
    ) -> "Entity":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            short_id_key (str): short_id_key 参数。
            title_key (str): title_key 参数。
            type_key (str): type_key 参数。
            description_key (str): description_key 参数。
            description_embedding_key (str): description_embedding_key 参数。
            name_embedding_key (str): name_embedding_key 参数。
            graph_embedding_key (str): graph_embedding_key 参数。
            community_key (str): community_key 参数。
            text_unit_ids_key (str): text_unit_ids_key 参数。
            document_ids_key (str): document_ids_key 参数。
            rank_key (str): rank_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return Entity(
            id=d[id_key],
            title=d[title_key],
            short_id=d.get(short_id_key),
            type=d.get(type_key),
            description=d.get(description_key),
            name_embedding=d.get(name_embedding_key),
            description_embedding=d.get(description_embedding_key),
            graph_embedding=d.get(graph_embedding_key),
            community_ids=d.get(community_key),
            rank=d.get(rank_key, 1),
            text_unit_ids=d.get(text_unit_ids_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
