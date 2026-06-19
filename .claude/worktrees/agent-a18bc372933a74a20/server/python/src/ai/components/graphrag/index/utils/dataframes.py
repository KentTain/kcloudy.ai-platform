"""包含DataFrame工具函数的模块."""

from collections.abc import Callable
from typing import Any, cast

import pandas as pd
from pandas._typing import MergeHow


def drop_columns(df: pd.DataFrame, *column: str) -> pd.DataFrame:
    """从数据框中删除列."""
    return df.drop(list(column), axis=1)


def where_column_equals(df: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
    """返回一个过滤后的DataFrame,其中某列等于指定值."""
    return cast("pd.DataFrame", df[df[column] == value])


def antijoin(df: pd.DataFrame, exclude: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    处理antijoin。

    Args:
        df (pd.DataFrame): df 参数。
        exclude (pd.DataFrame): exclude 参数。
        column (str): column 参数。

    Returns:
        处理结果。
    """
    result = df.merge(
        exclude[[column]],
        on=column,
        how="outer",
        indicator=True,
    )
    if "_merge" in result.columns:
        result = result[result["_merge"] == "left_only"].drop("_merge", axis=1)
    return cast("pd.DataFrame", result)


def transform_series(series: pd.Series, fn: Callable[[Any], Any]) -> pd.Series:
    """对序列应用转换函数."""
    return cast("pd.Series", series.apply(fn))


def join(
    left: pd.DataFrame, right: pd.DataFrame, key: str, strategy: MergeHow = "left"
) -> pd.DataFrame:
    """执行表连接操作."""
    return left.merge(right, on=key, how=strategy)


def union(*frames: pd.DataFrame) -> pd.DataFrame:
    """对给定的数据框集合执行合并操作."""
    return pd.concat(list(frames))


def select(df: pd.DataFrame, *columns: str) -> pd.DataFrame:
    """从数据框中选择列."""
    return cast("pd.DataFrame", df[list(columns)])
