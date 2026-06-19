"""提供图谱检索增强生成工具相关功能。"""

import re
from collections import defaultdict

from framework.configs.settings import get_settings

pattern = re.compile(r"\[\^Data:(\w+?)\((\d+(?:,\d+)*)\)\]")


def get_reference(text: str) -> dict:
    """
    获取reference。

    Args:
        text (str): text 参数。

    Returns:
        处理结果。
    """
    data_dict = defaultdict(set)
    for match in pattern.finditer(text):
        key = match.group(1).lower()
        value = match.group(2)

        ids = value.replace(" ", "").split(",")
        data_dict[key].update(ids)

    return dict(data_dict)


def generate_ref_links(data: dict[str, set[int]], index_id: str) -> str:
    """
    生成generate_ref_links。

    Args:
        data (dict[str, set[int]]): data 参数。
        index_id (str): index_id 参数。

    Returns:
        处理结果。
    """
    settings = get_settings()
    base_url = f"http://{settings.server.host}:{settings.server.port}/v1/references"
    lines = []
    for key, values in data.items():
        for value in values:
            lines.append(
                f"[^Data:{key.capitalize()}({value})]: [{key.capitalize()}: {value}]({base_url}/{index_id}/{key}/{value})"
            )
    return "\n".join(lines)
