"""
存储模块

提供 MinIO、阿里云 OSS、腾讯云 COS 等对象存储实现。
"""

from framework.storage.factory import get_storage_provider

__all__ = [
    "get_storage_provider",
]
