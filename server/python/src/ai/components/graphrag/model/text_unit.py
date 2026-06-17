"""包含 'TextUnit' 模型的包。

A package containing the 'TextUnit' model.
"""

from dataclasses import dataclass
from typing import Any

from ai.components.graphrag.model.identified import Identified


@dataclass
class TextUnit(Identified):
    """
    文档数据库中的文本单元项协议。

    文本单元是文档的基本组成部分,通常是文档分块后的结果。
    每个文本单元包含文本内容,嵌入向量以及与其相关的实体和关系。

    A protocol for a TextUnit item in a Document database.
    """

    text: str
    """文本单元的文本内容。

    The text of the unit.
    """

    text_embedding: list[float] | None = None
    """文本单元的文本嵌入向量(可选)。

    The text embedding for the text unit (optional).
    """

    entity_ids: list[str] | None = None
    """与文本单元相关的实体 ID 列表(可选)。

    List of entity IDs related to the text unit (optional).
    """

    relationship_ids: list[str] | None = None
    """与文本单元相关的关系 ID 列表(可选)。

    List of relationship IDs related to the text unit (optional).
    """

    covariate_ids: dict[str, list[str]] | None = None
    """与文本单元相关的不同类型的协变量字典(可选)。

    Dictionary of different types of covariates related to the text unit (optional).
    """

    n_tokens: int | None = None
    """文本中的 token 数量(可选)。

    The number of tokens in the text (optional).
    """

    document_ids: list[str] | None = None
    """文本单元出现的文档 ID 列表(可选)。

    List of document IDs in which the text unit appears (optional).
    """

    attributes: dict[str, Any] | None = None
    """与文本单元关联的其他属性字典(可选)。

    A dictionary of additional attributes associated with the text unit (optional).
    """

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        text_key: str = "text",
        text_embedding_key: str = "text_embedding",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        covariates_key: str = "covariate_ids",
        n_tokens_key: str = "n_tokens",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "TextUnit":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            short_id_key (str): short_id_key 参数。
            text_key (str): text_key 参数。
            text_embedding_key (str): text_embedding_key 参数。
            entities_key (str): entities_key 参数。
            relationships_key (str): relationships_key 参数。
            covariates_key (str): covariates_key 参数。
            n_tokens_key (str): n_tokens_key 参数。
            document_ids_key (str): document_ids_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return TextUnit(
            id=d[id_key],
            short_id=d.get(short_id_key),
            text=d[text_key],
            text_embedding=d.get(text_embedding_key),
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            covariate_ids=d.get(covariates_key),
            n_tokens=d.get(n_tokens_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
