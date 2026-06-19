"""包含 create_graph,_get_node_attributes,_get_edge_attributes 和 _get_attribute_column_mapping 方法定义的模块."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from ai.components.graphrag.index.utils.ds_util import get_required_input_table


@verb(name="compute_edge_combined_degree")
def compute_edge_combined_degree(
    input: VerbInput,
    to: str = "rank",
    node_name_column: str = "title",
    node_degree_column: str = "degree",
    edge_source_column: str = "source",
    edge_target_column: str = "target",
    **_kwargs,
) -> TableContainer:
    """
    处理compute_edge_combined_degree。

    Args:
        input (VerbInput): input 参数。
        to (str): to 参数。
        node_name_column (str): node_name_column 参数。
        node_degree_column (str): node_degree_column 参数。
        edge_source_column (str): edge_source_column 参数。
        edge_target_column (str): edge_target_column 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    edge_df: pd.DataFrame = cast("pd.DataFrame", input.get_input())
    if to in edge_df.columns:
        return TableContainer(table=edge_df)
    node_degree_df = _get_node_degree_table(input, node_name_column, node_degree_column)

    def join_to_degree(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        处理join_degree。

        Args:
            df (pd.DataFrame): df 参数。
            column (str): column 参数。

        Returns:
            处理结果。
        """
        degree_column = _degree_colname(column)
        result = df.merge(
            node_degree_df.rename(
                columns={node_name_column: column, node_degree_column: degree_column}
            ),
            on=column,
            how="left",
        )
        result[degree_column] = result[degree_column].fillna(0)
        return result

    edge_df = join_to_degree(edge_df, edge_source_column)
    edge_df = join_to_degree(edge_df, edge_target_column)
    edge_df[to] = (
        edge_df[_degree_colname(edge_source_column)]
        + edge_df[_degree_colname(edge_target_column)]
    )

    return TableContainer(table=edge_df)


def _degree_colname(column: str) -> str:
    """
    处理degree_colname。

    Args:
        column (str): column 参数。

    Returns:
        处理结果。
    """
    return f"{column}_degree"


def _get_node_degree_table(
    input: VerbInput, node_name_column: str, node_degree_column: str
) -> pd.DataFrame:
    """
    获取node_degree_table。

    Args:
        input (VerbInput): input 参数。
        node_name_column (str): node_name_column 参数。
        node_degree_column (str): node_degree_column 参数。

    Returns:
        处理结果。
    """
    nodes_container = get_required_input_table(input, "nodes")
    nodes = cast("pd.DataFrame", nodes_container.table)
    return cast("pd.DataFrame", nodes[[node_name_column, node_degree_column]])
