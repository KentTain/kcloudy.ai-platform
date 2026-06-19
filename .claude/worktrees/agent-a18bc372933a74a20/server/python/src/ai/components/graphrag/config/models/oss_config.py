"""默认配置的参数设置."""

from pydantic import BaseModel, Field


class OssConfig(BaseModel):
    """OSS 的默认配置部分."""

    endpoint: str | None = Field(description="OSS 的 MinIO 端点。", default=None)
    """OSS 的 MinIO 端点."""

    access_key: str | None = Field(description="OSS 的 MinIO 访问密钥。", default=None)
    """OSS 的 MinIO 访问密钥."""

    secret_key: str | None = Field(description="OSS 的 MinIO 密钥。", default=None)
    """OSS 的 MinIO 密钥."""

    container_name: str | None = Field(description="OSS 的存储桶名称", default=None)
    """OSS 的存储桶名称."""

    secure: bool = Field(description="是否对 MinIO 连接使用 HTTPS。", default=True)
    """是否对 OSS 连接使用 HTTPS."""

    region: str | None = Field(description="OSS 的 OSS 区域。", default=None)
    """OSS 的 OSS 区域."""

    enable_virtual_style_endpoint: bool | None = Field(
        description="是否启用 OSS 的虚拟样式端点。目前阿里云和腾讯云对象存储都只能是 enable_virtual_style_endpoint 访问方式，而 minio 默认必须是 disable_virtual_style_endpoint 方式",
        default=None,
    )
