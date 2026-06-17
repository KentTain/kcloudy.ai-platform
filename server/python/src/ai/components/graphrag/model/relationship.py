"""包含 'Relationship' 模型的包。

A package containing the 'Relationship' model.
"""

from dataclasses import dataclass
from typing import Any

from ai.components.graphrag.model.identified import Identified


@dataclass
class Relationship(Identified):
    """
    两个实体之间的关系。

    这是一个通用的关系模型,可用于表示任意两个实体之间的任何类型的关系。

    A relationship between two entities. This is a generic relationship, and can be used
    to represent any type of relationship between any two entities.
    """

    source: str
    """源实体的名称。

    The source entity name.
    """

    target: str
    """目标实体的名称。

    The target entity name.
    """

    weight: float | None = 1.0
    """边的权重。

    The edge weight.
    """

    description: str | None = None
    """关系的描述(可选)。

    A description of the relationship (optional).
    """

    description_embedding: list[float] | None = None
    """关系描述的语义嵌入向量(可选)。

    The semantic embedding for the relationship description (optional).
    """

    text_unit_ids: list[str] | None = None
    """关系出现的文本单元 ID 列表(可选)。

    List of text unit IDs in which the relationship appears (optional).
    """

    document_ids: list[str] | None = None
    """关系出现的文档 ID 列表(可选)。

    List of document IDs in which the relationship appears (optional).
    """

    attributes: dict[str, Any] | None = None
    """与关系关联的其他属性(可选)。这些属性将包含在搜索提示词中。

    Additional attributes associated with the relationship (optional).
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
        source_key: str = "source",
        target_key: str = "target",
        description_key: str = "description",
        weight_key: str = "weight",
        text_unit_ids_key: str = "text_unit_ids",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "Relationship":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            short_id_key (str): short_id_key 参数。
            source_key (str): source_key 参数。
            target_key (str): target_key 参数。
            description_key (str): description_key 参数。
            weight_key (str): weight_key 参数。
            text_unit_ids_key (str): text_unit_ids_key 参数。
            document_ids_key (str): document_ids_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return Relationship(
            id=d[id_key],
            short_id=d.get(short_id_key),
            source=d[source_key],
            target=d[target_key],
            description=d.get(description_key),
            weight=d.get(weight_key, 1.0),
            text_unit_ids=d.get(text_unit_ids_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
