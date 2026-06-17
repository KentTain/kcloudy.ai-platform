"""包含 create_graph,_get_node_attributes,_get_edge_attributes 和 _get_attribute_column_mapping 方法定义的模块."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.graph.extractors.community_reports.schemas import (
    CLAIM_DESCRIPTION,
    CLAIM_DETAILS,
    CLAIM_ID,
    CLAIM_STATUS,
    CLAIM_SUBJECT,
    CLAIM_TYPE,
)

_MISSING_DESCRIPTION = "No Description"


@verb(name="prepare_community_reports_claims")
def prepare_community_reports_claims(
    input: VerbInput,
    to: str = CLAIM_DETAILS,
    id_column: str = CLAIM_ID,
    description_column: str = CLAIM_DESCRIPTION,
    subject_column: str = CLAIM_SUBJECT,
    type_column: str = CLAIM_TYPE,
    status_column: str = CLAIM_STATUS,
    **_kwargs,
) -> TableContainer:
    """
    处理prepare_community_reports_claims。

    Args:
        input (VerbInput): input 参数。
        to (str): to 参数。
        id_column (str): id_column 参数。
        description_column (str): description_column 参数。
        subject_column (str): subject_column 参数。
        type_column (str): type_column 参数。
        status_column (str): status_column 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    claim_df: pd.DataFrame = cast("pd.DataFrame", input.get_input())
    claim_df = claim_df.fillna(value={description_column: _MISSING_DESCRIPTION})

    # merge values of five columns into a map column
    claim_df[to] = claim_df.apply(
        lambda x: {
            id_column: x[id_column],
            subject_column: x[subject_column],
            type_column: x[type_column],
            status_column: x[status_column],
            description_column: x[description_column],
        },
        axis=1,
    )

    return TableContainer(table=claim_df)
