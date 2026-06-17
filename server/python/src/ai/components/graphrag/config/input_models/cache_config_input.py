"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict

from ai.components.graphrag.config.enums import CacheType


class CacheConfigInput(TypedDict):
    """缓存的默认配置部分."""

    type: NotRequired[CacheType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
    storage_account_blob_url: NotRequired[str | None]
