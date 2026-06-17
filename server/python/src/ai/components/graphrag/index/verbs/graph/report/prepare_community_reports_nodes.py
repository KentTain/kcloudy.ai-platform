"""包含 create_graph,_get_node_attributes,_get_edge_attributes 和 _get_attribute_column_mapping 方法定义的模块."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.graph.extractors.community_reports.schemas import (
    NODE_DEGREE,
    NODE_DESCRIPTION,
    NODE_DETAILS,
    NODE_ID,
    NODE_NAME,
)

_MISSING_DESCRIPTION = "No Description"


@verb(name="prepare_community_reports_nodes")
def prepare_community_reports_nodes(
    input: VerbInput,
    to: str = NODE_DETAILS,
    id_column: str = NODE_ID,
    name_column: str = NODE_NAME,
    description_column: str = NODE_DESCRIPTION,
    degree_column: str = NODE_DEGREE,
    **_kwargs,
) -> TableContainer:
    """
    处理prepare_community_reports_nodes。

    Args:
        input (VerbInput): input 参数。
        to (str): to 参数。
        id_column (str): id_column 参数。
        name_column (str): name_column 参数。
        description_column (str): description_column 参数。
        degree_column (str): degree_column 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    node_df = cast("pd.DataFrame", input.get_input())
    node_df = node_df.fillna(value={description_column: _MISSING_DESCRIPTION})

    # merge values of four columns into a map column
    node_df[to] = node_df.apply(
        lambda x: {
            id_column: x[id_column],
            name_column: x[name_column],
            description_column: x[description_column],
            degree_column: x[degree_column],
        },
        axis=1,
    )
    return TableContainer(table=node_df)
