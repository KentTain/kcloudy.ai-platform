"""
工具函数模块

包含字符串、时间日期、枚举、字典、JSON、树形结构、日志等工具函数。
"""

from framework.utils.dictionary_util import (
    deep_merge,
    keys_to_camel_case,
    keys_to_snake_case,
)
from framework.utils.enum_util import get_enum_values, is_valid_enum_value
from framework.utils.json_util import json_dumps, json_loads
from framework.utils.log_util import (
    Color,
    Icon,
    format_timestamp,
    write_completion_message,
    write_empty_line,
    write_error,
    write_info,
    write_separator,
    write_step_header,
    write_success,
    write_title,
    write_warning,
)
from framework.utils.string_util import mask_string, to_camel_case, to_snake_case
from framework.utils.time_util import (
    format_datetime,
    humanize_time,
    timestamp_to_datetime,
)
from framework.utils.tree_util import TreeUtil

__all__ = [
    "to_snake_case",
    "to_camel_case",
    "mask_string",
    "format_datetime",
    "timestamp_to_datetime",
    "humanize_time",
    "get_enum_values",
    "is_valid_enum_value",
    "deep_merge",
    "keys_to_snake_case",
    "keys_to_camel_case",
    "json_dumps",
    "json_loads",
    "TreeUtil",
    # 日志工具
    "write_info",
    "write_success",
    "write_warning",
    "write_error",
    "write_separator",
    "write_title",
    "write_step_header",
    "write_empty_line",
    "write_completion_message",
    "format_timestamp",
    "Color",
    "Icon",
]
