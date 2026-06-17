"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict

from ai.components.graphrag.config.enums import StorageType


class StorageConfigInput(TypedDict):
    """存储的默认配置部分."""

    type: NotRequired[StorageType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
    storage_account_blob_url: NotRequired[str | None]
    # MinIO 特定配置
    endpoint: NotRequired[str | None]
    access_key: NotRequired[str | None]
    secret_key: NotRequired[str | None]
    secure: NotRequired[bool | None]
    region: NotRequired[str | None]
    enable_virtual_style_endpoint: NotRequired[bool | None]
