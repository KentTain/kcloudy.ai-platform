"""哈希工具."""

from collections.abc import Iterable
from hashlib import md5
from typing import Any


def gen_md5_hash(item: dict[str, Any], hashcode: Iterable[str]):
    """生成MD5哈希值."""
    hashed = "".join([str(item[column]) for column in hashcode])
    return f"{md5(hashed.encode('utf-8'), usedforsecurity=False).hexdigest()}"
