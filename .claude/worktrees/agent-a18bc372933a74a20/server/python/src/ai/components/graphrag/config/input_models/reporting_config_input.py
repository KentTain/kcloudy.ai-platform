"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict

from ai.components.graphrag.config.enums import ReportingType


class ReportingConfigInput(TypedDict):
    """报告的默认配置部分."""

    type: NotRequired[ReportingType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
    storage_account_blob_url: NotRequired[str | None]
