"""包含 'Document' 模型的包。

A package containing the 'Document' model.
"""

from dataclasses import dataclass, field
from typing import Any

from ai.components.graphrag.model.named import Named


@dataclass
class Document(Named):
    """
    系统中文档的协议。

    表示知识库中的文档,包含文档的原始内容,摘要,嵌入向量等信息。

    A protocol for a document in the system.
    """

    type: str = "text"
    """文档的类型。

    Type of the document.
    """

    text_unit_ids: list[str] = field(default_factory=list)
    """文档中的文本单元列表。

    list of text units in the document.
    """

    raw_content: str = ""
    """文档的��始文本内容。

    The raw text content of the document.
    """

    summary: str | None = None
    """文档的摘要(可选)。

    Summary of the document (optional).
    """

    summary_embedding: list[float] | None = None
    """文档摘要的语义嵌入向量(可选)。

    The semantic embedding for the document summary (optional).
    """

    raw_content_embedding: list[float] | None = None
    """文档原始内容的语义嵌入向量(可选)。

    The semantic embedding for the document raw content (optional).
    """

    attributes: dict[str, Any] | None = None
    """结构化属性字典,例如作者等(可选)。

    A dictionary of structured attributes such as author, etc (optional).
    """

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        title_key: str = "title",
        type_key: str = "type",
        raw_content_key: str = "raw_content",
        summary_key: str = "summary",
        summary_embedding_key: str = "summary_embedding",
        raw_content_embedding_key: str = "raw_content_embedding",
        text_units_key: str = "text_units",
        attributes_key: str = "attributes",
    ) -> "Document":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            short_id_key (str): short_id_key 参数。
            title_key (str): title_key 参数。
            type_key (str): type_key 参数。
            raw_content_key (str): raw_content_key 参数。
            summary_key (str): summary_key 参数。
            summary_embedding_key (str): summary_embedding_key 参数。
            raw_content_embedding_key (str): raw_content_embedding_key 参数。
            text_units_key (str): text_units_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return Document(
            id=d[id_key],
            short_id=d.get(short_id_key),
            title=d[title_key],
            type=d.get(type_key, "text"),
            raw_content=d[raw_content_key],
            summary=d.get(summary_key),
            summary_embedding=d.get(summary_embedding_key),
            raw_content_embedding=d.get(raw_content_embedding_key),
            text_unit_ids=d.get(text_units_key, []),
            attributes=d.get(attributes_key),
        )
