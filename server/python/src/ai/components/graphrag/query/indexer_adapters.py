"""索引引擎到查询的读取适配器。

理想情况下,这些函数中进行类型适配,重命名,整理等的部分最终应该消失。
理想情况下,这只是直接读取到对象模型中。

Indexing-Engine to Query Read Adapters.

The parts of these functions that do type adaptation, renaming, collating, etc. should eventually go away.
Ideally this is just a straight read-thorugh into the object model.
"""

from typing import cast

import pandas as pd

from ai.components.graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from ai.components.graphrag.query.input.loaders.dfs import (
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
)


def read_indexer_text_units(final_text_units: pd.DataFrame) -> list[TextUnit]:
    """
    从原始索引输出中读取文本单元。

    Read in the Text Units from the raw indexing outputs.

    参数 Parameters
    ----------
    - final_text_units (pd.DataFrame): 最终文本单元的 DataFrame。DataFrame of final text units

    返回 Returns
    -------
    - list[TextUnit]: 文本单元对象列表。List of TextUnit objects
    """
    return read_text_units(
        df=final_text_units,
        short_id_col=None,
        # 期望协变量映射的类型为 type -> ids
        # expects a covariate map of type -> ids
        covariates_col=None,
    )


def read_indexer_covariates(final_covariates: pd.DataFrame) -> list[Covariate]:
    """
    从原始索引输出中读取协变量(声明)。

    Read in the Claims from the raw indexing outputs.

    参数 Parameters
    ----------
    - final_covariates (pd.DataFrame): 最终协变量的 DataFrame。DataFrame of final covariates

    返回 Returns
    -------
    - list[Covariate]: 协变量对象列表。List of Covariate objects
    """
    # 转换 ID 为字符串类型
    # Convert ID to string type
    covariate_df = final_covariates
    covariate_df["id"] = covariate_df["id"].astype(str)
    return read_covariates(
        df=covariate_df,
        short_id_col="human_readable_id",
        attributes_cols=[
            "object_id",
            "status",
            "start_date",
            "end_date",
            "description",
        ],
        text_unit_ids_col=None,
    )


def read_indexer_relationships(final_relationships: pd.DataFrame) -> list[Relationship]:
    """
    从原始索引输出中读取关系。

    Read in the Relationships from the raw indexing outputs.

    参数 Parameters
    ----------
    - final_relationships (pd.DataFrame): 最终关系的 DataFrame。DataFrame of final relationships

    返回 Returns
    -------
    - list[Relationship]: 关系对象列表。List of Relationship objects
    """
    return read_relationships(
        df=final_relationships,
        short_id_col="human_readable_id",
        description_embedding_col=None,
        document_ids_col=None,
        attributes_cols=["rank"],
    )


def read_indexer_reports(
    final_community_reports: pd.DataFrame,
    final_nodes: pd.DataFrame,
    community_level: int,
) -> list[CommunityReport]:
    """
    从原始索引输出中读取社区报告。

    Read in the Community Reports from the raw indexing outputs.

    参数 Parameters
    ----------
    - final_community_reports (pd.DataFrame): 最终社区报告的 DataFrame。DataFrame of final community reports
    - final_nodes (pd.DataFrame): 最终节点的 DataFrame。DataFrame of final nodes
    - community_level (int): 社区层级过滤阈值。Community level filter threshold

    返回 Returns
    -------
    - list[CommunityReport]: 社区报告对象列表。List of CommunityReport objects
    """
    report_df = final_community_reports
    entity_df = final_nodes
    # 过滤指定社区层级以下的实体
    # Filter entities under specified community level
    entity_df = _filter_under_community_level(entity_df, community_level)
    # 填充缺失的社区值为 -1 并转换为整数
    # Fill missing community values with -1 and convert to integer
    entity_df["community"] = entity_df["community"].fillna(-1)
    entity_df["community"] = entity_df["community"].astype(int)

    # 按标题分组并获取最大社区值
    # Group by title and get maximum community value
    entity_df = entity_df.groupby(["title"]).agg({"community": "max"}).reset_index()
    entity_df["community"] = entity_df["community"].astype(str)
    filtered_community_df = entity_df["community"].drop_duplicates()

    # 过滤社区报告并与过滤后的社区合并
    # Filter community reports and merge with filtered communities
    report_df = _filter_under_community_level(report_df, community_level)
    report_df = report_df.merge(filtered_community_df, on="community", how="inner")

    return read_community_reports(
        df=report_df,
        id_col="community",
        short_id_col="community",
        summary_embedding_col=None,
        content_embedding_col=None,
    )


def read_indexer_entities(
    final_nodes: pd.DataFrame,
    final_entities: pd.DataFrame,
    community_level: int,
) -> list[Entity]:
    """
    从原始索引输出中读取实体。

    Read in the Entities from the raw indexing outputs.

    参数 Parameters
    ----------
    - final_nodes (pd.DataFrame): 最终节点的 DataFrame。DataFrame of final nodes
    - final_entities (pd.DataFrame): 最终实体的 DataFrame。DataFrame of final entities
    - community_level (int): 社区层级过滤阈值。Community level filter threshold

    返回 Returns
    -------
    - list[Entity]: 实体对象列表。List of Entity objects
    """
    entity_df = final_nodes
    entity_embedding_df = final_entities

    # 过滤指定社区层级以下的实体
    # Filter entities under specified community level
    entity_df = _filter_under_community_level(entity_df, community_level)
    # 选择并重命名列
    # Select and rename columns
    entity_df = cast(
        "pd.DataFrame", entity_df[["title", "degree", "community"]]
    ).rename(columns={"title": "name", "degree": "rank"})

    # 处理缺失值和类型转换
    # Handle missing values and type conversion
    entity_df["community"] = entity_df["community"].fillna(-1)
    entity_df["community"] = entity_df["community"].astype(int)
    entity_df["rank"] = entity_df["rank"].astype(int)

    # 对于重复的实体,保留具有最高社区层级的实体
    # for duplicate entities, keep the one with the highest community level
    entity_df = (
        entity_df.groupby(["name", "rank"]).agg({"community": "max"}).reset_index()
    )
    entity_df["community"] = entity_df["community"].apply(lambda x: [str(x)])
    # 与实体嵌入数据合并并去重
    # Merge with entity embedding data and deduplicate
    entity_df = entity_df.merge(
        entity_embedding_df, on="name", how="inner"
    ).drop_duplicates(subset=["name"])

    # 将实体 DataFrame 读取为知识模型对象
    # read entity dataframe to knowledge model objects
    return read_entities(
        df=entity_df,
        id_col="id",
        title_col="name",
        type_col="type",
        short_id_col="human_readable_id",
        description_col="description",
        community_col="community",
        rank_col="rank",
        name_embedding_col=None,
        description_embedding_col="description_embedding",
        graph_embedding_col=None,
        text_unit_ids_col="text_unit_ids",
        document_ids_col=None,
    )


def _filter_under_community_level(
    df: pd.DataFrame, community_level: int
) -> pd.DataFrame:
    """
    过滤指定社区层级以下的数据。

    Filter data under specified community level.

    参数 Parameters
    ----------
    - df (pd.DataFrame): 输入的 DataFrame。Input DataFrame
    - community_level (int): 社区层级阈值。Community level threshold

    返回 Returns
    -------
    - pd.DataFrame: 过滤后的 DataFrame。Filtered DataFrame
    """
    return cast(
        "pd.DataFrame",
        df[df.level <= community_level],
    )
