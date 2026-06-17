"""包含create_community_reports和load_strategy方法定义的模块."""

import logging
from typing import cast

import pandas as pd

from ai.components.graphrag.index.graph.extractors.community_reports import schemas
from ai.components.graphrag.index.graph.extractors.community_reports.build_mixed_context import (
    build_mixed_context,
)
from ai.components.graphrag.index.graph.extractors.community_reports.sort_context import (
    sort_context,
)
from ai.components.graphrag.index.graph.extractors.community_reports.utils import (
    set_context_size,
)
from ai.components.graphrag.index.utils.dataframes import (
    antijoin,
    drop_columns,
    join,
    select,
    transform_series,
    union,
    where_column_equals,
)

log = logging.getLogger(__name__)


def prep_community_report_context(
    report_df: pd.DataFrame | None,
    community_hierarchy_df: pd.DataFrame,
    local_context_df: pd.DataFrame,
    level: int | str,
    max_tokens: int,
) -> pd.DataFrame:
    """
    为给定级别的每个社区准备上下文。

    对于每个社区:
    - 检查本地上下文是否在限制内,如果是,使用本地上下文
    - 如果本地上下文超过限制,从最大的子社区开始,迭代地用子社区报告替换本地上下文
    """
    if report_df is None:
        report_df = pd.DataFrame()

    level = int(level)
    level_context_df = _at_level(level, local_context_df)
    valid_context_df = _within_context(level_context_df)
    invalid_context_df = _exceeding_context(level_context_df)

    # 没有报告可以替换,所以我们只是修剪无效上下文记录的本地上下文
    # 这种情况应该只发生在社区层次结构的最底层,那里没有子社区
    if invalid_context_df.empty:
        return valid_context_df

    if report_df.empty:
        invalid_context_df[schemas.CONTEXT_STRING] = _sort_and_trim_context(
            invalid_context_df, max_tokens
        )
        set_context_size(invalid_context_df)
        invalid_context_df[schemas.CONTEXT_EXCEED_FLAG] = 0
        return union(valid_context_df, invalid_context_df)

    level_context_df = _antijoin_reports(level_context_df, report_df)

    # 对于每个无效上下文,我们将尝试用子社区报告替换
    # 首先获取每个子社区的本地上下文和报告(如果可用)
    sub_context_df = _get_subcontext_df(level + 1, report_df, local_context_df)
    community_df = _get_community_df(
        level, invalid_context_df, sub_context_df, community_hierarchy_df, max_tokens
    )

    # 处理任何无法用子社区报告替换的剩余无效记录
    # 这种情况应该很少见,但如果发生,我们将只是修剪本地上下文以适应限制
    remaining_df = _antijoin_reports(invalid_context_df, community_df)
    remaining_df[schemas.CONTEXT_STRING] = _sort_and_trim_context(
        remaining_df, max_tokens
    )

    result = union(valid_context_df, community_df, remaining_df)
    set_context_size(result)
    result[schemas.CONTEXT_EXCEED_FLAG] = 0
    return result


def _drop_community_level(df: pd.DataFrame) -> pd.DataFrame:
    """从数据框中删除社区级别列."""
    return drop_columns(df, schemas.COMMUNITY_LEVEL)


def _at_level(level: int, df: pd.DataFrame) -> pd.DataFrame:
    """返回给定级别的记录."""
    return where_column_equals(df, schemas.COMMUNITY_LEVEL, level)


def _exceeding_context(df: pd.DataFrame) -> pd.DataFrame:
    """返回上下文超过限制的记录."""
    return where_column_equals(df, schemas.CONTEXT_EXCEED_FLAG, 1)


def _within_context(df: pd.DataFrame) -> pd.DataFrame:
    """返回上下文在限制内的记录."""
    return where_column_equals(df, schemas.CONTEXT_EXCEED_FLAG, 0)


def _antijoin_reports(df: pd.DataFrame, reports: pd.DataFrame) -> pd.DataFrame:
    """返回df中不在reports中的记录."""
    return antijoin(df, reports, schemas.NODE_COMMUNITY)


def _sort_and_trim_context(df: pd.DataFrame, max_tokens: int) -> pd.Series:
    """排序并修剪上下文以适应限制."""
    series = cast("pd.Series", df[schemas.ALL_CONTEXT])
    return transform_series(series, lambda x: sort_context(x, max_tokens=max_tokens))


def _build_mixed_context(df: pd.DataFrame, max_tokens: int) -> pd.Series:
    """排序并修剪上下文以适应限制."""
    series = cast("pd.Series", df[schemas.ALL_CONTEXT])
    return transform_series(
        series, lambda x: build_mixed_context(x, max_tokens=max_tokens)
    )


def _get_subcontext_df(
    level: int, report_df: pd.DataFrame, local_context_df: pd.DataFrame
) -> pd.DataFrame:
    """获取每个社区的子社区上下文."""
    sub_report_df = _drop_community_level(_at_level(level, report_df))
    sub_context_df = _at_level(level, local_context_df)
    sub_context_df = join(sub_context_df, sub_report_df, schemas.NODE_COMMUNITY)
    sub_context_df.rename(
        columns={schemas.NODE_COMMUNITY: schemas.SUB_COMMUNITY}, inplace=True
    )
    return sub_context_df


def _get_community_df(
    level: int,
    invalid_context_df: pd.DataFrame,
    sub_context_df: pd.DataFrame,
    community_hierarchy_df: pd.DataFrame,
    max_tokens: int,
) -> pd.DataFrame:
    """获取每个社区的社区上下文."""
    # 为每个社区收集所有子社区的上下文
    community_df = _drop_community_level(_at_level(level, community_hierarchy_df))
    invalid_community_ids = select(invalid_context_df, schemas.NODE_COMMUNITY)
    subcontext_selection = select(
        sub_context_df,
        schemas.SUB_COMMUNITY,
        schemas.FULL_CONTENT,
        schemas.ALL_CONTEXT,
        schemas.CONTEXT_SIZE,
    )

    invalid_communities = join(
        community_df, invalid_community_ids, schemas.NODE_COMMUNITY, "inner"
    )
    community_df = join(
        invalid_communities, subcontext_selection, schemas.SUB_COMMUNITY
    )
    community_df[schemas.ALL_CONTEXT] = community_df.apply(
        lambda x: {
            schemas.SUB_COMMUNITY: x[schemas.SUB_COMMUNITY],
            schemas.ALL_CONTEXT: x[schemas.ALL_CONTEXT],
            schemas.FULL_CONTENT: x[schemas.FULL_CONTENT],
            schemas.CONTEXT_SIZE: x[schemas.CONTEXT_SIZE],
        },
        axis=1,
    )
    community_df = (
        community_df.groupby(schemas.NODE_COMMUNITY)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )
    community_df[schemas.CONTEXT_STRING] = _build_mixed_context(
        community_df, max_tokens
    )
    community_df[schemas.COMMUNITY_LEVEL] = level
    return community_df
