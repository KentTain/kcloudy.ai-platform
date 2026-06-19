"""包含'PipelineStorageConfig','PipelineFileStorageConfig'和'PipelineMemoryStorageConfig'模型的模块."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from ai.components.graphrag.config.enums import StorageType

T = TypeVar("T")


class PipelineStorageConfig(BaseModel, Generic[T]):
    """表示管道的存储配置."""

    type: T


class PipelineFileStorageConfig(PipelineStorageConfig[Literal[StorageType.file]]):
    """表示管道的文件存储配置."""

    type: Literal[StorageType.file] = StorageType.file
    """存储的类型."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the storage.", default=None
    )
    """存储的基础目录."""


class PipelineMemoryStorageConfig(PipelineStorageConfig[Literal[StorageType.memory]]):
    """表示管道的内存存储配置."""

    type: Literal[StorageType.memory] = StorageType.memory
    """存储的类型."""


class PipelineBlobStorageConfig(PipelineStorageConfig[Literal[StorageType.blob]]):
    """表示管道的blob存储配置."""

    type: Literal[StorageType.blob] = StorageType.blob
    """存储的类型."""

    connection_string: str | None = pydantic_Field(
        description="The blob storage connection string for the storage.", default=None
    )
    """存储的blob存储连接字符串."""

    container_name: str = pydantic_Field(
        description="The container name for storage", default=None
    )
    """存储的容器名称."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the storage.", default=None
    )
    """存储的基础目录."""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url.", default=None
    )
    """存储账户blob URL."""


class PipelineMinioStorageConfig(PipelineStorageConfig[Literal[StorageType.minio]]):
    """表示管道的MinIO S3兼容存储配置."""

    type: Literal[StorageType.minio] = StorageType.minio
    """存储的类型."""

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


PipelineStorageConfigTypes = (
    PipelineFileStorageConfig
    | PipelineMemoryStorageConfig
    | PipelineBlobStorageConfig
    | PipelineMinioStorageConfig
)
