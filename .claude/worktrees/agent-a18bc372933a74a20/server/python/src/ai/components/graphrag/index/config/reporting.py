"""包含'PipelineReportingConfig','PipelineFileReportingConfig'和'PipelineConsoleReportingConfig'模型的模块."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from ai.components.graphrag.config.enums import ReportingType

T = TypeVar("T")


class PipelineReportingConfig(BaseModel, Generic[T]):
    """表示管道的报告配置."""

    type: T


class PipelineFileReportingConfig(PipelineReportingConfig[Literal[ReportingType.file]]):
    """表示管道的文件报告配置."""

    type: Literal[ReportingType.file] = ReportingType.file
    """报告的类型."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the reporting.", default=None
    )
    """报告的基础目录."""


class PipelineConsoleReportingConfig(
    PipelineReportingConfig[Literal[ReportingType.console]]
):
    """表示管道的控制台报告配置."""

    type: Literal[ReportingType.console] = ReportingType.console
    """报告的类型."""


class PipelineBlobReportingConfig(PipelineReportingConfig[Literal[ReportingType.blob]]):
    """表示管道的blob报告配置."""

    type: Literal[ReportingType.blob] = ReportingType.blob
    """报告的类型."""

    connection_string: str | None = pydantic_Field(
        description="The blob reporting connection string for the reporting.",
        default=None,
    )
    """报告的blob报告连接字符串."""

    container_name: str = pydantic_Field(
        description="The container name for reporting", default=None
    )
    """报告的容器名称"""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url for reporting", default=None
    )
    """报告的存储账户blob URL"""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the reporting.", default=None
    )
    """报告的基础目录."""


class PipelineMinioReportingConfig(
    PipelineReportingConfig[Literal[ReportingType.minio]]
):
    """表示管道的MinIO报告配置."""

    type: Literal[ReportingType.minio] = ReportingType.minio
    """报告的类型."""
    endpoint: str = pydantic_Field(description="The MinIO endpoint for the storage.")
    """存储的MinIO端点."""

    access_key: str = pydantic_Field(
        description="The MinIO access key for the storage."
    )
    """存储的MinIO访问密钥."""

    secret_key: str = pydantic_Field(
        description="The MinIO secret key for the storage."
    )
    """存储的MinIO秘密密钥."""

    container_name: str = pydantic_Field(description="The bucket name for storage")
    """存储的桶名称."""

    secure: bool = pydantic_Field(
        description="Whether to use HTTPS for MinIO connection.", default=True
    )
    """是否对MinIO连接使用HTTPS."""

    region: str | None = pydantic_Field(
        description="The MinIO region for the storage.", default=None
    )
    """存储的MinIO区域."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the storage.", default=None
    )
    """存储的基础目录."""

    enable_virtual_style_endpoint: bool | None = pydantic_Field(
        description="Whether to enable virtual style endpoint for oss. 目前阿里云和腾讯云对象存储都只能是enable_virtual_style_endpoint访问方式, 而minio默认必须是disable_virtual_style_endpoint方式",
        default=None,
    )


PipelineReportingConfigTypes = (
    PipelineFileReportingConfig
    | PipelineConsoleReportingConfig
    | PipelineBlobReportingConfig
    | PipelineMinioReportingConfig
)
