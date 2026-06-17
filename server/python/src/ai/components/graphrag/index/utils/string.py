"""字符串工具."""

import html
import re
from typing import Any


def clean_str(input: Any) -> str:
    """通过删除HTML转义字符,控制字符和其他不需要的字符来清理输入字符串."""
    # 如果获得非字符串输入,直接返回
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)
