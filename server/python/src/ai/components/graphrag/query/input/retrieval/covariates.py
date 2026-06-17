"""从协变量集合中检索数据的工具函数。

Util functions to retrieve covariates from a collection.
"""

from typing import Any, cast

import pandas as pd

from ai.components.graphrag.model import Covariate, Entity


def get_candidate_covariates(
    selected_entities: list[Entity],
    covariates: list[Covariate],
) -> list[Covariate]:
    """
    获取与选定实体相关的所有协变量。

    Get all covariates that are related to selected entities.

    参数 Parameters
    ----------
    - selected_entities (list[Entity]): 选定的实体列表。Selected entities list
    - covariates (list[Covariate]): 协变量列表。Covariates list

    返回 Returns
    -------
    - list[Covariate]: 与选定实体相关的协变量列表。Covariates related to selected entities
    """
    # 提取选定实体的标题 / Extract titles of selected entities
    selected_entity_names = [entity.title for entity in selected_entities]
    # 过滤与选定实体相关的协变量 / Filter covariates related to selected entities
    return [
        covariate
        for covariate in covariates
        if covariate.subject_id in selected_entity_names
    ]


def to_covariate_dataframe(covariates: list[Covariate]) -> pd.DataFrame:
    """
    将协变量集合转换为 Pandas 数据框。

    Convert a list of covariates to a pandas dataframe.

    参数 Parameters
    ----------
    - covariates (list[Covariate]): 协变量列表。Covariates list

    返回 Returns
    -------
    - pd.DataFrame: 包含协变量数据的数据框。Dataframe containing covariate data
    """
    if len(covariates) == 0:
        return pd.DataFrame()

    # 添加表头 / add header
    header = ["id", "entity"]
    attributes = covariates[0].attributes or {} if len(covariates) > 0 else {}
    attribute_cols = list(attributes.keys()) if len(covariates) > 0 else []
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for covariate in covariates:
        new_record = [
            covariate.short_id if covariate.short_id else "",
            covariate.subject_id,
        ]
        # 添加属性值 / Add attribute values
        for field in attribute_cols:
            field_value = (
                str(covariate.attributes.get(field))
                if covariate.attributes and covariate.attributes.get(field)
                else ""
            )
            new_record.append(field_value)
        records.append(new_record)
    return pd.DataFrame(records, columns=cast("Any", header))
