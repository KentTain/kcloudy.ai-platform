"""包含'PipelineCacheConfig','PipelineFileCacheConfig'和'PipelineMemoryCacheConfig'模型的模块."""

from __future__ import annotations

from enum import Enum


class CacheType(str, Enum):
    """流水线的缓存配置类型."""

    file = "file"
    """文件缓存配置类型."""
    memory = "memory"
    """内存缓存配置类型."""
    none = "none"
    """无缓存配置类型."""
    blob = "blob"
    """blob缓存配置类型."""
    minio = "minio"
    """minio缓存配置类型."""

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'


class InputFileType(str, Enum):
    """流水线的输入文件类型."""

    csv = "csv"
    """CSV输入类型."""
    text = "text"
    """文本输入类型."""

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'


class InputType(str, Enum):
    """流水线的输入类型."""

    file = "file"
    """文件存储类型."""
    blob = "blob"
    """blob存储类型."""
    minio = "minio"
    """minio存储类型."""

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'


class StorageType(str, Enum):
    """流水线的存储类型."""

    file = "file"
    """文件存储类型."""
    memory = "memory"
    """内存存储类型."""
    blob = "blob"
    """blob存储类型."""
    minio = "minio"
    """MinIO S3兼容存储类型."""

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'


class ReportingType(str, Enum):
    """流水线的报告配置类型."""

    file = "file"
    """文件报告配置类型."""
    console = "console"
    """控制台报告配置类型."""
    blob = "blob"
    """blob报告配置类型."""
    minio = "minio"
    """minio报告配置类型."""

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'


class TextEmbeddingTarget(str, Enum):
    """用于文本嵌入的目标."""

    all = "all"
    required = "required"

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'


class LLMType(str, Enum):
    """LLM类型枚举类定义."""

    # 嵌入
    OpenAIEmbedding = "openai_embedding"
    AzureOpenAIEmbedding = "azure_openai_embedding"

    # 原始补全
    OpenAI = "openai"
    AzureOpenAI = "azure_openai"

    # 聊天补全
    OpenAIChat = "openai_chat"
    AzureOpenAIChat = "azure_openai_chat"

    # 调试
    StaticResponse = "static_response"

    def __repr__(self):
        """获取字符串表示形式."""
        return f'"{self.value}"'
