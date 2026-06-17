"""包含'PipelineCacheConfig','PipelineFileCacheConfig'和'PipelineMemoryCacheConfig'模型的模块."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from ai.components.graphrag.config.enums import CacheType

T = TypeVar("T")


class PipelineCacheConfig(BaseModel, Generic[T]):
    """表示管道的缓存配置."""

    type: T


class PipelineFileCacheConfig(PipelineCacheConfig[Literal[CacheType.file]]):
    """表示管道的文件缓存配置."""

    type: Literal[CacheType.file] = CacheType.file
    """缓存的类型."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """缓存的基础目录."""


class PipelineMemoryCacheConfig(PipelineCacheConfig[Literal[CacheType.memory]]):
    """表示管道的内存缓存配置."""

    type: Literal[CacheType.memory] = CacheType.memory
    """缓存的类型."""


class PipelineNoneCacheConfig(PipelineCacheConfig[Literal[CacheType.none]]):
    """表示管道的无缓存配置."""

    type: Literal[CacheType.none] = CacheType.none
    """缓存的类型."""


class PipelineBlobCacheConfig(PipelineCacheConfig[Literal[CacheType.blob]]):
    """表示管道的blob缓存配置."""

    type: Literal[CacheType.blob] = CacheType.blob
    """缓存的类型."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """缓存的基础目录."""

    connection_string: str | None = pydantic_Field(
        description="The blob cache connection string for the cache.", default=None
    )
    """缓存的blob缓存连接字符串."""

    container_name: str = pydantic_Field(
        description="The container name for cache", default=None
    )
    """缓存的容器名称"""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url for cache", default=None
    )
    """缓存的存储账户blob URL"""


class PipelineMinioCacheConfig(PipelineCacheConfig[Literal[CacheType.minio]]):
    """表示管道的MinIO缓存配置."""

    type: Literal[CacheType.minio] = CacheType.minio
    """存储的类型."""

    endpoint: str = pydantic_Field(description="The MinIO endpoint for the cache.")
    """缓存的MinIO端点."""

    access_key: str = pydantic_Field(description="The MinIO access key for the cache.")
    """缓存的MinIO访问密钥."""

    secret_key: str = pydantic_Field(description="The MinIO secret key for the cache.")
    """缓存的MinIO秘密密钥."""

    container_name: str = pydantic_Field(description="The bucket name for cache")
    """缓存的桶名称."""

    secure: bool = pydantic_Field(
        description="Whether to use HTTPS for MinIO connection.", default=True
    )
    """是否对MinIO连接使用HTTPS."""

    region: str | None = pydantic_Field(
        description="The MinIO region for the cache.", default=None
    )
    """缓存的MinIO区域."""

    enable_virtual_style_endpoint: bool | None = pydantic_Field(
        description="Whether to enable virtual style endpoint for oss. 目前阿里云和腾讯云对象存储都只能是enable_virtual_style_endpoint访问方式, 而minio默认必须是disable_virtual_style_endpoint方式",
        default=None,
    )

    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """缓存的基础目录."""


PipelineCacheConfigTypes = (
    PipelineFileCacheConfig
    | PipelineMemoryCacheConfig
    | PipelineBlobCacheConfig
    | PipelineNoneCacheConfig
    | PipelineMinioCacheConfig
)
