"""
租户资源类型枚举
"""

from enum import Enum


class DatabaseType(str, Enum):
    """数据库类型"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"


class StorageType(str, Enum):
    """存储类型"""

    MINIO = "minio"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    LOCAL = "local"


class QueueType(str, Enum):
    """队列类型"""

    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"


class PubSubType(str, Enum):
    """发布订阅类型"""

    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"


class CacheType(str, Enum):
    """缓存类型"""

    REDIS = "redis"
    MEMCACHED = "memcached"


class NoSqlType(str, Enum):
    """NoSQL 类型"""

    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"


class VodType(str, Enum):
    """视频点播类型"""

    ALIYUN = "aliyun"
    TENCENT = "tencent"


class CodeType(str, Enum):
    """代码执行环境类型"""

    LOCAL = "local"
    SANDBOX = "sandbox"
