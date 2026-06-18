"""
资源配置 Schema

定义数据库、存储、缓存、队列、发布订阅配置的请求和响应模型。
"""

from datetime import datetime
from typing import Any

from framework.schemas.base import BasePaginatedQuery, BaseQuery
from pydantic import BaseModel, Field


# =============================================================================
# 通用响应模型
# =============================================================================


class ResourceQuery(BaseQuery):
    """资源列表查询参数（非分页）"""

    keyword: str | None = Field(None, max_length=100, description="搜索关键词")


class ResourcePaginatedQuery(ResourceQuery, BasePaginatedQuery):
    """资源列表查询参数（分页）"""

    pass


class ConnectionTestResult(BaseModel):
    """连接测试结果"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="测试结果消息")
    latency_ms: int | None = Field(None, description="延迟（毫秒）")


# =============================================================================
# 数据库配置 Schema
# =============================================================================


class DatabaseConfigCreate(BaseModel):
    """创建数据库配置请求"""

    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    type: str = Field(..., min_length=1, max_length=20, description="数据库类型")
    host: str = Field(..., min_length=1, max_length=255, description="数据库主机")
    port: int = Field(..., ge=1, le=65535, description="数据库端口")
    database: str = Field(..., min_length=1, max_length=100, description="数据库名称")
    username: str = Field(..., min_length=1, max_length=100, description="数据库用户名")
    password: str = Field(..., min_length=1, description="数据库密码")


class DatabaseConfigUpdate(BaseModel):
    """更新数据库配置请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="配置名称")
    type: str | None = Field(None, min_length=1, max_length=20, description="数据库类型")
    host: str | None = Field(None, min_length=1, max_length=255, description="数据库主机")
    port: int | None = Field(None, ge=1, le=65535, description="数据库端口")
    database: str | None = Field(None, min_length=1, max_length=100, description="数据库名称")
    username: str | None = Field(None, min_length=1, max_length=100, description="数据库用户名")
    password: str | None = Field(None, min_length=1, description="数据库密码")


class DatabasePropertyResponse(BaseModel):
    """数据库配置响应"""

    id: str = Field(..., description="配置 ID")
    name: str = Field(..., description="配置名称")
    type: str = Field(..., description="数据库类型")
    host: str = Field(..., description="数据库主机")
    port: int = Field(..., description="数据库端口")
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码（脱敏）")
    is_default: bool = Field(..., description="是否为默认配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DatabasePropertyPaginatedListResponse(BaseModel):
    """数据库配置分页列表响应"""

    items: list[DatabasePropertyResponse] = Field(
        default_factory=list, description="配置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 存储配置 Schema
# =============================================================================


class StorageConfigCreate(BaseModel):
    """创建存储配置请求"""

    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    type: str = Field(..., min_length=1, max_length=20, description="存储类型")
    bucket: str = Field(..., min_length=1, max_length=100, description="存储桶名称")
    endpoint: str | None = Field(None, max_length=255, description="服务端点")
    access_key: str | None = Field(None, max_length=100, description="访问密钥")
    secret_key: str | None = Field(None, description="私密密钥")


class StorageConfigUpdate(BaseModel):
    """更新存储配置请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="配置名称")
    type: str | None = Field(None, min_length=1, max_length=20, description="存储类型")
    bucket: str | None = Field(None, min_length=1, max_length=100, description="存储桶名称")
    endpoint: str | None = Field(None, max_length=255, description="服务端点")
    access_key: str | None = Field(None, max_length=100, description="访问密钥")
    secret_key: str | None = Field(None, description="私密密钥")


class StoragePropertyResponse(BaseModel):
    """存储配置响应"""

    id: str = Field(..., description="配置 ID")
    name: str = Field(..., description="配置名称")
    type: str = Field(..., description="存储类型")
    bucket: str = Field(..., description="存储桶名称")
    endpoint: str | None = Field(None, description="服务端点")
    access_key: str | None = Field(None, description="访问密钥")
    secret_key: str | None = Field(None, description="私密密钥（脱敏）")
    is_default: bool = Field(..., description="是否为默认配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class StoragePropertyPaginatedListResponse(BaseModel):
    """存储配置分页列表响应"""

    items: list[StoragePropertyResponse] = Field(
        default_factory=list, description="配置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 缓存配置 Schema
# =============================================================================


class CacheConfigCreate(BaseModel):
    """创建缓存配置请求"""

    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    host: str = Field(..., min_length=1, max_length=255, description="缓存主机")
    port: int = Field(..., ge=1, le=65535, description="缓存端口")
    password: str | None = Field(None, description="缓存密码")
    db: int = Field(0, ge=0, le=15, description="数据库编号")
    prefix: str | None = Field(None, max_length=50, description="键前缀")


class CacheConfigUpdate(BaseModel):
    """更新缓存配置请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="配置名称")
    host: str | None = Field(None, min_length=1, max_length=255, description="缓存主机")
    port: int | None = Field(None, ge=1, le=65535, description="缓存端口")
    password: str | None = Field(None, description="缓存密码")
    db: int | None = Field(None, ge=0, le=15, description="数据库编号")
    prefix: str | None = Field(None, max_length=50, description="键前缀")


class CachePropertyResponse(BaseModel):
    """缓存配置响应"""

    id: str = Field(..., description="配置 ID")
    name: str = Field(..., description="配置名称")
    host: str = Field(..., description="缓存主机")
    port: int = Field(..., description="缓存端口")
    password: str | None = Field(None, description="缓存密码（脱敏）")
    db: int = Field(..., description="数据库编号")
    prefix: str | None = Field(None, description="键前缀")
    is_default: bool = Field(..., description="是否为默认配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CachePropertyPaginatedListResponse(BaseModel):
    """缓存配置分页列表响应"""

    items: list[CachePropertyResponse] = Field(
        default_factory=list, description="配置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 队列配置 Schema
# =============================================================================


class QueueConfigCreate(BaseModel):
    """创建队列配置请求"""

    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    type: str = Field(..., min_length=1, max_length=20, description="队列类型")
    host: str = Field(..., min_length=1, max_length=255, description="队列主机")
    port: int = Field(..., ge=1, le=65535, description="队列端口")
    username: str | None = Field(None, max_length=100, description="用户名")
    password: str | None = Field(None, description="密码")
    vhost: str | None = Field(None, max_length=100, description="虚拟主机")


class QueueConfigUpdate(BaseModel):
    """更新队列配置请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="配置名称")
    type: str | None = Field(None, min_length=1, max_length=20, description="队列类型")
    host: str | None = Field(None, min_length=1, max_length=255, description="队列主机")
    port: int | None = Field(None, ge=1, le=65535, description="队列端口")
    username: str | None = Field(None, max_length=100, description="用户名")
    password: str | None = Field(None, description="密码")
    vhost: str | None = Field(None, max_length=100, description="虚拟主机")


class QueuePropertyResponse(BaseModel):
    """队列配置响应"""

    id: str = Field(..., description="配置 ID")
    name: str = Field(..., description="配置名称")
    type: str = Field(..., description="队列类型")
    host: str = Field(..., description="队列主机")
    port: int = Field(..., description="队列端口")
    username: str | None = Field(None, description="用户名")
    password: str | None = Field(None, description="密码（脱敏）")
    vhost: str | None = Field(None, description="虚拟主机")
    is_default: bool = Field(..., description="是否为默认配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class QueuePropertyPaginatedListResponse(BaseModel):
    """队列配置分页列表响应"""

    items: list[QueuePropertyResponse] = Field(
        default_factory=list, description="配置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


# =============================================================================
# 发布订阅配置 Schema
# =============================================================================


class PubSubConfigCreate(BaseModel):
    """创建发布订阅配置请求"""

    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    type: str = Field(..., min_length=1, max_length=20, description="发布订阅类型")
    host: str = Field(..., min_length=1, max_length=255, description="主机地址")
    port: int = Field(..., ge=1, le=65535, description="端口")
    username: str | None = Field(None, max_length=100, description="用户名")
    password: str | None = Field(None, description="密码")


class PubSubConfigUpdate(BaseModel):
    """更新发布订阅配置请求"""

    name: str | None = Field(None, min_length=1, max_length=100, description="配置名称")
    type: str | None = Field(None, min_length=1, max_length=20, description="发布订阅类型")
    host: str | None = Field(None, min_length=1, max_length=255, description="主机地址")
    port: int | None = Field(None, ge=1, le=65535, description="端口")
    username: str | None = Field(None, max_length=100, description="用户名")
    password: str | None = Field(None, description="密码")


class PubSubPropertyResponse(BaseModel):
    """发布订阅配置响应"""

    id: str = Field(..., description="配置 ID")
    name: str = Field(..., description="配置名称")
    type: str = Field(..., description="发布订阅类型")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    username: str | None = Field(None, description="用户名")
    password: str | None = Field(None, description="密码（脱敏）")
    is_default: bool = Field(..., description="是否为默认配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class PubSubPropertyPaginatedListResponse(BaseModel):
    """发布订阅配置分页列表响应"""

    items: list[PubSubPropertyResponse] = Field(
        default_factory=list, description="配置列表"
    )
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")
