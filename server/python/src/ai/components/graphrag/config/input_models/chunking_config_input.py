"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class ChunkingConfigInput(TypedDict):
    """分块的配置部分."""

    size: NotRequired[int | str | None]
    overlap: NotRequired[int | str | None]
    group_by_columns: NotRequired[list[str] | str | None]
    strategy: NotRequired[dict | None]
