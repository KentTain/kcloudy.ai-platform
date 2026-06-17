"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict

from ai.components.graphrag.config.enums import InputFileType, InputType


class InputConfigInput(TypedDict):
    """输入的默认配置部分."""

    type: NotRequired[InputType | str | None]
    file_type: NotRequired[InputFileType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
    file_encoding: NotRequired[str | None]
    file_pattern: NotRequired[str | None]
    source_column: NotRequired[str | None]
    timestamp_column: NotRequired[str | None]
    timestamp_format: NotRequired[str | None]
    text_column: NotRequired[str | None]
    title_column: NotRequired[str | None]
    document_attribute_columns: NotRequired[list[str] | str | None]
    storage_account_blob_url: NotRequired[str | None]
