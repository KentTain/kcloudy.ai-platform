"""
存储工厂

根据配置返回对应的存储实现。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.configs.settings import OssSettings
    from framework.core.storage import StorageProvider


def get_storage_provider(config: "OssSettings") -> "StorageProvider":
    """
    获取存储提供者

    Args:
        config: OSS 配置

    Returns:
        StorageProvider: 存储提供者实例

    Raises:
        ValueError: 不支持的存储类型
    """
    storage_type = config.default_type.lower()

    match storage_type:
        case "minio":
            from framework.storage.impl.minio import MinioStorage
            return MinioStorage(config.minio)
        case "aliyun":
            from framework.storage.impl.aliyun import AliyunStorage
            return AliyunStorage(config.aliyun)
        case "tencent":
            from framework.storage.impl.tencent import TencentStorage
            return TencentStorage(config.tencent)
        case _:
            raise ValueError(f"不支持的存储类型: {storage_type}")
