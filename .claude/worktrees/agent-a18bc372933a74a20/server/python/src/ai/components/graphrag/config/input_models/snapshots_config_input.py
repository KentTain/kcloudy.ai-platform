"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class SnapshotsConfigInput(TypedDict):
    """快照的配置部分."""

    graphml: NotRequired[bool | str | None]
    raw_entities: NotRequired[bool | str | None]
    top_level_nodes: NotRequired[bool | str | None]
