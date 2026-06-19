"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.enums import InputFileType, InputType


class InputConfig(BaseModel):
    """输入的默认配置部分."""

    type: InputType = Field(description="要使用的输入类型。", default=defs.INPUT_TYPE)
    file_type: InputFileType = Field(
        description="要使用的输入文件类型。", default=defs.INPUT_FILE_TYPE
    )
    base_dir: str = Field(
        description="要使用的输入基础目录。", default=defs.INPUT_BASE_DIR
    )
    connection_string: str | None = Field(
        description="要使用的 Azure Blob 存储连接字符串。", default=None
    )
    storage_account_blob_url: str | None = Field(
        description="要使用的存储账户 blob URL。", default=None
    )
    container_name: str | None = Field(
        description="要使用的 Azure Blob 存储容器名称。", default=None
    )
    encoding: str | None = Field(
        description="要使用的输入文件编码。",
        default=defs.INPUT_FILE_ENCODING,
    )
    file_pattern: str = Field(
        description="要使用的输入文件模式。", default=defs.INPUT_TEXT_PATTERN
    )
    file_filter: dict[str, str] | None = Field(
        description="输入文件的可选文件过滤器。", default=None
    )
    source_column: str | None = Field(description="要使用的输入源列。", default=None)
    timestamp_column: str | None = Field(
        description="要使用的输入时间戳列。", default=None
    )
    timestamp_format: str | None = Field(
        description="要使用的输入时间戳格式。", default=None
    )
    text_column: str = Field(
        description="要使用的输入文本列。", default=defs.INPUT_TEXT_COLUMN
    )
    title_column: str | None = Field(description="要使用的输入标题列。", default=None)
    document_attribute_columns: list[str] = Field(
        description="要使用的文档属性列。", default=[]
    )
    # MinIO
    endpoint: str | None = Field(description="存储的 MinIO 端点。", default=None)
    """存储的 MinIO 端点."""

    access_key: str | None = Field(description="存储的 MinIO 访问密钥。", default=None)
    """存储的 MinIO 访问密钥."""

    secret_key: str | None = Field(description="存储的 MinIO 密钥。", default=None)
    """存储的 MinIO 密钥."""

    secure: bool | None = Field(
        description="是否对 MinIO 连接使用 HTTPS。", default=True
    )
    """是否对 MinIO 连接使用 HTTPS."""

    region: str | None = Field(description="输入的 MinIO 区域。", default=None)
    """输入的 MinIO 区域."""

    enable_virtual_style_endpoint: bool | None = Field(
        description="是否启用 OSS 的虚拟样式端点。目前阿里云和腾讯云对象存储都只能是 enable_virtual_style_endpoint 访问方式，而 minio 默认必须是 disable_virtual_style_endpoint 方式",
        default=None,
    )
