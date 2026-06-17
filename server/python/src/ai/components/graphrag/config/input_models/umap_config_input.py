"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class UmapConfigInput(TypedDict):
    """UMAP 的配置部分."""

    enabled: NotRequired[bool | str | None]
