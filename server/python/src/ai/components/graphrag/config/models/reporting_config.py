"""默认配置的参数设置."""

from pydantic import BaseModel, Field

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.enums import ReportingType


class ReportingConfig(BaseModel):
    """报告的默认配置部分."""

    type: ReportingType = Field(
        description="要使用的报告类型。", default=defs.REPORTING_TYPE
    )
    base_dir: str = Field(
        description="报告的基础目录。",
        default=defs.REPORTING_BASE_DIR,
    )
    connection_string: str | None = Field(
        description="要使用的报告连接字符串。", default=None
    )
    container_name: str | None = Field(
        description="要使用的报告容器名称。", default=None
    )
    storage_account_blob_url: str | None = Field(
        description="要使用的存储账户 blob URL。", default=None
    )
    # MinIO specific configuration
    endpoint: str | None = Field(description="要使用的 MinIO 端点。", default=None)
    access_key: str | None = Field(
        description="要使用的 MinIO 访问密钥。", default=None
    )
    secret_key: str | None = Field(description="要使用的 MinIO 密钥。", default=None)
    secure: bool | None = Field(
        description="是否对 MinIO 连接使用 HTTPS。", default=True
    )
    region: str | None = Field(description="要使用的 MinIO 区域。", default=None)
    enable_virtual_style_endpoint: bool | None = Field(
        description="是否启用 OSS 的虚拟样式端点。目前阿里云和腾讯云对象存储都只能是 enable_virtual_style_endpoint 访问方式，而 minio 默认必须是 disable_virtual_style_endpoint 方式",
        default=None,
    )
