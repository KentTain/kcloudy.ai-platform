"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class GlobalSearchConfigInput(TypedDict):
    """全局搜索的默认配置部分."""

    max_tokens: NotRequired[int | str | None]
    data_max_tokens: NotRequired[int | str | None]
    map_max_tokens: NotRequired[int | str | None]
    reduce_max_tokens: NotRequired[int | str | None]
    concurrency: NotRequired[int | str | None]
