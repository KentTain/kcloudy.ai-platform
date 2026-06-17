"""包含 'Covariate' 模型的包。

A package containing the 'Covariate' model.
"""

from dataclasses import dataclass
from typing import Any

from ai.components.graphrag.model.identified import Identified


@dataclass
class Covariate(Identified):
    """
    系统中协变量的协议。

    协变量是与主体(subject)关联的元数据,例如实体的声明(claims)。
    每个主体(例如实体)可以关联多种类型的协变量。

    A protocol for a covariate in the system.

    Covariates are metadata associated with a subject, e.g. entity claims.
    Each subject (e.g. entity) may be associated with multiple types of covariates.
    """

    subject_id: str
    """主体的 ID。

    The subject id.
    """

    subject_type: str = "entity"
    """主体的类型。

    The subject type.
    """

    covariate_type: str = "claim"
    """协变量的类型。

    The covariate type.
    """

    text_unit_ids: list[str] | None = None
    """协变量信息出现的文本单元 ID 列表(可选)。

    List of text unit IDs in which the covariate info appears (optional).
    """

    document_ids: list[str] | None = None
    """协变量信息出现的文档 ID 列表(可选)。

    List of document IDs in which the covariate info appears (optional).
    """

    attributes: dict[str, Any] | None = None
    """与协变量关联的其他属性字典(可选)。

    Additional attributes associated with the covariate (optional).
    """

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        subject_id_key: str = "subject_id",
        subject_type_key: str = "subject_type",
        covariate_type_key: str = "covariate_type",
        short_id_key: str = "short_id",
        text_unit_ids_key: str = "text_unit_ids",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "Covariate":
        """
        处理dict。

        Args:
            d (dict[str, Any]): d 参数。
            id_key (str): id_key 参数。
            subject_id_key (str): subject_id_key 参数。
            subject_type_key (str): subject_type_key 参数。
            covariate_type_key (str): covariate_type_key 参数。
            short_id_key (str): short_id_key 参数。
            text_unit_ids_key (str): text_unit_ids_key 参数。
            document_ids_key (str): document_ids_key 参数。
            attributes_key (str): attributes_key 参数。

        Returns:
            处理结果。
        """
        return Covariate(
            id=d[id_key],
            short_id=d.get(short_id_key),
            subject_id=d[subject_id_key],
            subject_type=d.get(subject_type_key, "entity"),
            covariate_type=d.get(covariate_type_key, "claim"),
            text_unit_ids=d.get(text_unit_ids_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
