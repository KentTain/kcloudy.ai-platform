"""数据加载工具。

Data load utils.
"""

import numpy as np
import pandas as pd


def to_str(data: pd.Series, column_name: str | None) -> str:
    """
    将值转换并验证为字符串。

    Convert and validate a value to a string.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name

    返回 Returns
    -------
    - str: 字符串值。String value

    异常 Raises
    ------
    - ValueError: 如果列名为 None 或列不存在。If column name is None or column not found
    """
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        return str(data[column_name])
    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_optional_str(data: pd.Series, column_name: str | None) -> str | None:
    """
    将值转换并验证为可选字符串。

    Convert and validate a value to an optional string.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name

    返回 Returns
    -------
    - str | None: 字符串值或 None。String value or None

    异常 Raises
    ------
    - ValueError: 如果列名为 None 或列不存在。If column name is None or column not found
    """
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        return str(data[column_name])
    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_list(
    data: pd.Series, column_name: str | None, item_type: type | None = None
) -> list:
    """
    将值转换并验证为列表。

    Convert and validate a value to a list.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name
    - item_type (type | None): 列表项类型。Item type for list items

    返回 Returns
    -------
    - list: 列表值。List value

    异常 Raises
    ------
    - ValueError: 如果列名为 None,列不存在或值不是列表。If column name is None, column not found, or value is not a list
    - TypeError: 如果列表项类型不匹配。If list item type does not match
    """
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        # 将 numpy 数组转换为列表 / Convert numpy array to list
        if isinstance(value, np.ndarray):
            value = value.tolist()

        if not isinstance(value, list):
            msg = f"value is not a list: {value} ({type(value)})"
            raise ValueError(msg)

        # 验证列表项类型 / Validate list item types
        if item_type is not None:
            for v in value:
                if not isinstance(v, item_type):
                    msg = f"list item has item that is not {item_type}: {v} ({type(v)})"
                    raise TypeError(msg)
        return value

    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_optional_list(
    data: pd.Series, column_name: str | None, item_type: type | None = None
) -> list | None:
    """
    将值转换并验证为可选列表。

    Convert and validate a value to an optional list.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name
    - item_type (type | None): 列表项类型。Item type for list items

    返回 Returns
    -------
    - list | None: 列表值或 None。List value or None

    异常 Raises
    ------
    - ValueError: 如果值不是列表。If value is not a list
    - TypeError: 如果列表项类型不匹配。If list item type does not match
    """
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]  # type: ignore
        if value is None:
            return None

        # 将 numpy 数组转换为列表 / Convert numpy array to list
        if isinstance(value, np.ndarray):
            value = value.tolist()

        if not isinstance(value, list):
            msg = f"value is not a list: {value} ({type(value)})"
            raise ValueError(msg)

        # 验证列表项类型 / Validate list item types
        if item_type is not None:
            for v in value:
                if not isinstance(v, item_type):
                    msg = f"list item has item that is not {item_type}: {v} ({type(v)})"
                    raise TypeError(msg)
        return value

    return None


def to_int(data: pd.Series, column_name: str | None) -> int:
    """
    将值转换并验证为整数。

    Convert and validate a value to an int.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name

    返回 Returns
    -------
    - int: 整数值。Integer value

    异常 Raises
    ------
    - ValueError: 如果列名为 None,列不存在或值不是整数。If column name is None, column not found, or value is not an int
    """
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        # 将浮点数转换为整数 / Convert float to int
        if isinstance(value, float):
            value = int(value)
        if not isinstance(value, int):
            msg = f"value is not an int: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return int(value)


def to_optional_int(data: pd.Series, column_name: str | None) -> int | None:
    """
    将值转换并验证为可选整数。

    Convert and validate a value to an optional int.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name

    返回 Returns
    -------
    - int | None: 整数值或 None。Integer value or None

    异常 Raises
    ------
    - ValueError: 如果列不存在或值不是整数。If column not found or value is not an int
    """
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]

        if value is None:
            return None

        # 将浮点数转换为整数 / Convert float to int
        if isinstance(value, float):
            value = int(value)
        if not isinstance(value, int):
            msg = f"value is not an int: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return int(value)


def to_float(data: pd.Series, column_name: str | None) -> float:
    """
    将值转换并验证为浮点数。

    Convert and validate a value to a float.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name

    返回 Returns
    -------
    - float: 浮点数值。Float value

    异常 Raises
    ------
    - ValueError: 如果列名为 None,列不存在或值不是浮点数。If column name is None, column not found, or value is not a float
    """
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if not isinstance(value, float):
            msg = f"value is not a float: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return float(value)


def to_optional_float(data: pd.Series, column_name: str | None) -> float | None:
    """
    将值转换并验证为可选浮点数。

    Convert and validate a value to an optional float.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name

    返回 Returns
    -------
    - float | None: 浮点数值或 None。Float value or None

    异常 Raises
    ------
    - ValueError: 如果列不存在或值不是浮点数。If column not found or value is not a float
    """
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        if not isinstance(value, float):
            msg = f"value is not a float: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return float(value)


def to_dict(
    data: pd.Series,
    column_name: str | None,
    key_type: type | None = None,
    value_type: type | None = None,
) -> dict:
    """
    将值转换并验证为字典。

    Convert and validate a value to a dict.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name
    - key_type (type | None): 字典键类型。Key type for dict keys
    - value_type (type | None): 字典值类型。Value type for dict values

    返回 Returns
    -------
    - dict: 字典值。Dictionary value

    异常 Raises
    ------
    - ValueError: 如果列名为 None,列不存在或值不是字典。If column name is None, column not found, or value is not a dict
    - TypeError: 如果字典键或值类型不匹配。If dict key or value type does not match
    """
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if not isinstance(value, dict):
            msg = f"value is not a dict: {value} ({type(value)})"
            raise ValueError(msg)

        # 验证字典键类型 / Validate dict key types
        if key_type is not None:
            for v in value:
                if not isinstance(v, key_type):
                    msg = f"dict key has item that is not {key_type}: {v} ({type(v)})"
                    raise TypeError(msg)

        # 验证字典值类型 / Validate dict value types
        if value_type is not None:
            for v in value.values():
                if not isinstance(v, value_type):
                    msg = (
                        f"dict value has item that is not {value_type}: {v} ({type(v)})"
                    )
                    raise TypeError(msg)
        return value

    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_optional_dict(
    data: pd.Series,
    column_name: str | None,
    key_type: type | None = None,
    value_type: type | None = None,
) -> dict | None:
    """
    将值转换并验证为可选字典。

    Convert and validate a value to an optional dict.

    参数 Parameters
    ----------
    - data (pd.Series): 数据行。Data row
    - column_name (str | None): 列名。Column name
    - key_type (type | None): 字典键类型。Key type for dict keys
    - value_type (type | None): 字典值类型。Value type for dict values

    返回 Returns
    -------
    - dict | None: 字典值或 None。Dictionary value or None

    异常 Raises
    ------
    - ValueError: 如果列不存在。If column not found
    - TypeError: 如果值不是字典或键/值类型不匹配。If value is not a dict or key/value type does not match
    """
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        if not isinstance(value, dict):
            msg = f"value is not a dict: {value} ({type(value)})"
            raise TypeError(msg)

        # 验证字典键类型 / Validate dict key types
        if key_type is not None:
            for v in value:
                if not isinstance(v, key_type):
                    msg = f"dict key has item that is not {key_type}: {v} ({type(v)})"
                    raise TypeError(msg)

        # 验证字典值类型 / Validate dict value types
        if value_type is not None:
            for v in value.values():
                if not isinstance(v, value_type):
                    msg = (
                        f"dict value has item that is not {value_type}: {v} ({type(v)})"
                    )
                    raise TypeError(msg)

        return value

    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)
