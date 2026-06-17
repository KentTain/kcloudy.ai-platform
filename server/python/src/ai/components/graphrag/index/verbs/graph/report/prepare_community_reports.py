"""包含 create_community_reports and load_strategy methods definition."""

import logging
from typing import cast

import pandas as pd
from datashaper import (
    TableContainer,
    VerbCallbacks,
    VerbInput,
    progress_iterable,
    verb,
)

from ai.components.graphrag.index.graph.extractors.community_reports import (
    filter_claims_to_nodes,
    filter_edges_to_nodes,
    filter_nodes_to_level,
    get_levels,
    schemas,
    set_context_exceeds_flag,
    set_context_size,
    sort_context,
)
from ai.components.graphrag.index.utils.ds_util import (
    get_named_input_table,
    get_required_input_table,
)

log = logging.getLogger(__name__)


@verb(name="prepare_community_reports")
def prepare_community_reports(
    input: VerbInput,
    callbacks: VerbCallbacks,
    max_tokens: int = 16_000,
    **_kwargs,
) -> TableContainer:
    """
    处理prepare_community_reports。

    Args:
        input (VerbInput): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        max_tokens (int): max_tokens 参数。
        _kwargs: _kwargs 参数。

    Returns:
        处理结果。
    """
    # Prepare Community Reports
    node_df = cast("pd.DataFrame", get_required_input_table(input, "nodes").table)
    edge_df = cast("pd.DataFrame", get_required_input_table(input, "edges").table)
    claim_df = get_named_input_table(input, "claims")
    if claim_df is not None:
        claim_df = cast("pd.DataFrame", claim_df.table)

    levels = get_levels(node_df, schemas.NODE_LEVEL)
    dfs = []

    for level in progress_iterable(levels, callbacks.progress, len(levels)):
        communities_at_level_df = _prepare_reports_at_level(
            node_df, edge_df, claim_df, level, max_tokens
        )
        dfs.append(communities_at_level_df)

    # build initial local context for all communities
    return TableContainer(table=pd.concat(dfs))


def _prepare_reports_at_level(
    node_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    claim_df: pd.DataFrame | None,
    level: int,
    max_tokens: int = 16_000,
    community_id_column: str = schemas.COMMUNITY_ID,
    node_id_column: str = schemas.NODE_ID,
    node_name_column: str = schemas.NODE_NAME,
    node_details_column: str = schemas.NODE_DETAILS,
    node_level_column: str = schemas.NODE_LEVEL,
    node_degree_column: str = schemas.NODE_DEGREE,
    node_community_column: str = schemas.NODE_COMMUNITY,
    edge_id_column: str = schemas.EDGE_ID,
    edge_source_column: str = schemas.EDGE_SOURCE,
    edge_target_column: str = schemas.EDGE_TARGET,
    edge_degree_column: str = schemas.EDGE_DEGREE,
    edge_details_column: str = schemas.EDGE_DETAILS,
    claim_id_column: str = schemas.CLAIM_ID,
    claim_subject_column: str = schemas.CLAIM_SUBJECT,
    claim_details_column: str = schemas.CLAIM_DETAILS,
):
    """
    处理prepare_reports_at_level。

    Args:
        node_df (pd.DataFrame): node_df 参数。
        edge_df (pd.DataFrame): edge_df 参数。
        claim_df (pd.DataFrame | None): claim_df 参数。
        level (int): level 参数。
        max_tokens (int): max_tokens 参数。
        community_id_column (str): community_id_column 参数。
        node_id_column (str): node_id_column 参数。
        node_name_column (str): node_name_column 参数。
        node_details_column (str): node_details_column 参数。
        node_level_column (str): node_level_column 参数。
        node_degree_column (str): node_degree_column 参数。
        node_community_column (str): node_community_column 参数。
        edge_id_column (str): edge_id_column 参数。
        edge_source_column (str): edge_source_column 参数。
        edge_target_column (str): edge_target_column 参数。
        edge_degree_column (str): edge_degree_column 参数。
        edge_details_column (str): edge_details_column 参数。
        claim_id_column (str): claim_id_column 参数。
        claim_subject_column (str): claim_subject_column 参数。
        claim_details_column (str): claim_details_column 参数。

    Returns:
        处理结果。
    """

    def get_edge_details(node_df: pd.DataFrame, edge_df: pd.DataFrame, name_col: str):
        """
        获取edge_details。

        Args:
            node_df (pd.DataFrame): node_df 参数。
            edge_df (pd.DataFrame): edge_df 参数。
            name_col (str): name_col 参数。

        Returns:
            处理结果。
        """
        return node_df.merge(
            cast(
                "pd.DataFrame",
                edge_df[[name_col, schemas.EDGE_DETAILS]],
            ).rename(columns={name_col: schemas.NODE_NAME}),
            on=schemas.NODE_NAME,
            how="left",
        )

    level_node_df = filter_nodes_to_level(node_df, level)
    log.info("Number of nodes at level=%s => %s", level, len(level_node_df))
    nodes = level_node_df[node_name_column].tolist()

    # Filter edges & claims to those containing the target nodes
    level_edge_df = filter_edges_to_nodes(edge_df, nodes)
    level_claim_df = (
        filter_claims_to_nodes(claim_df, nodes) if claim_df is not None else None
    )

    # concat all edge details per node
    merged_node_df = pd.concat(
        [
            get_edge_details(level_node_df, level_edge_df, edge_source_column),
            get_edge_details(level_node_df, level_edge_df, edge_target_column),
        ],
        axis=0,
    )
    merged_node_df = (
        merged_node_df.groupby(
            [
                node_name_column,
                node_community_column,
                node_degree_column,
                node_level_column,
            ]
        )
        .agg({node_details_column: "first", edge_details_column: list})
        .reset_index()
    )

    # concat claim details per node
    if level_claim_df is not None:
        merged_node_df = merged_node_df.merge(
            cast(
                "pd.DataFrame",
                level_claim_df[[claim_subject_column, claim_details_column]],
            ).rename(columns={claim_subject_column: node_name_column}),
            on=node_name_column,
            how="left",
        )
    merged_node_df = (
        merged_node_df.groupby(
            [
                node_name_column,
                node_community_column,
                node_level_column,
                node_degree_column,
            ]
        )
        .agg(
            {
                node_details_column: "first",
                edge_details_column: "first",
                **({claim_details_column: list} if level_claim_df is not None else {}),
            }
        )
        .reset_index()
    )

    # concat all node details, including name, degree, node_details, edge_details, and claim_details
    merged_node_df[schemas.ALL_CONTEXT] = merged_node_df.apply(
        lambda x: {
            node_name_column: x[node_name_column],
            node_degree_column: x[node_degree_column],
            node_details_column: x[node_details_column],
            edge_details_column: x[edge_details_column],
            claim_details_column: x[claim_details_column]
            if level_claim_df is not None
            else [],
        },
        axis=1,
    )

    # group all node details by community
    community_df = (
        merged_node_df.groupby(node_community_column)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )
    community_df[schemas.CONTEXT_STRING] = community_df[schemas.ALL_CONTEXT].apply(
        lambda x: sort_context(
            x,
            node_id_column=node_id_column,
            node_name_column=node_name_column,
            node_details_column=node_details_column,
            edge_id_column=edge_id_column,
            edge_details_column=edge_details_column,
            edge_degree_column=edge_degree_column,
            edge_source_column=edge_source_column,
            edge_target_column=edge_target_column,
            claim_id_column=claim_id_column,
            claim_details_column=claim_details_column,
            community_id_column=community_id_column,
        )
    )
    set_context_size(community_df)
    set_context_exceeds_flag(community_df, max_tokens)

    community_df[schemas.COMMUNITY_LEVEL] = level
    return community_df
