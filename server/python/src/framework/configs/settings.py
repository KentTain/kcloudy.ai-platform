"""
全局配置定义

包含所有配置项的类型安全定义。
"""

from pathlib import Path
from typing import Any

from pydantic import Field

from framework.configs.base import BaseSettings


# ==============================================================================
# 基础设施配置
# ==============================================================================

class ConnectionPoolSettings(BaseSettings):
    """连接池配置"""
    max_connections: int = Field(default=50, description="最大连接数")
    socket_timeout: float = Field(default=10.0, description="套接字超时时间")
    socket_connect_timeout: float = Field(default=5.0, description="连接超时时间")
    socket_keepalive: bool = Field(default=True, description="是否启用套接字保活")
    retry_on_timeout: bool = Field(default=True, description="超时时重试")
    health_check_interval: int = Field(default=30, description="健康检查间隔")


class RedisSingleSettings(BaseSettings):
    """Redis 单机配置"""
    host: str = Field(default="localhost", description="Redis 主机")
    port: int = Field(default=6379, description="Redis 端口")
    password: str = Field(default="", description="Redis 密码")
    db: int = Field(default=0, description="Redis 数据库")
    connection_pool: ConnectionPoolSettings | None = Field(
        default=None, description="连接池配置"
    )


class RedisSettings(BaseSettings):
    """Redis 配置"""
    mode: str = Field(default="single", description="模式: single/cluster/sentinel")
    single: RedisSingleSettings = Field(
        default_factory=RedisSingleSettings, description="单机配置"
    )


class SqlalchemyPoolSettings(BaseSettings):
    """SQLAlchemy 连接池配置"""
    echo: bool = Field(default=False, description="是否打印连接池日志")
    size: int = Field(default=20, description="连接池大小")
    max_overflow: int = Field(default=30, description="最大溢出连接数")


class SqlalchemySettings(BaseSettings):
    """数据库配置"""
    url: str = Field(default="", description="数据库连接 URL")
    echo: bool = Field(default=False, description="是否打印 SQL")
    pool: SqlalchemyPoolSettings = Field(
        default_factory=SqlalchemyPoolSettings, description="连接池配置"
    )


class MinioSettings(BaseSettings):
    """MinIO 配置"""
    endpoint: str = Field(default="", description="MinIO 端点")
    internal_endpoint: str = Field(default="", description="MinIO 内部端点")
    access_key: str = Field(default="", description="访问密钥")
    secret_key: str = Field(default="", description="秘密密钥")
    secure: bool = Field(default=False, description="是否使用 HTTPS")


class AliyunOssSettings(BaseSettings):
    """阿里云 OSS 配置"""
    endpoint: str = Field(default="", description="OSS 端点")
    internal_endpoint: str = Field(default="", description="OSS 内部端点")
    access_key_id: str = Field(default="", description="访问密钥 ID")
    access_key_secret: str = Field(default="", description="访问密钥秘钥")


class TencentCosSettings(BaseSettings):
    """腾讯云 COS 配置"""
    endpoint: str = Field(default="", description="COS 端点")
    internal_endpoint: str = Field(default="", description="COS 内部端点")
    secret_id: str = Field(default="", description="秘密 ID")
    secret_key: str = Field(default="", description="秘密密钥")
    region: str = Field(default="", description="区域")
    token: str = Field(default="", description="临时令牌")
    scheme: str = Field(default="https", description="协议类型")


class OssSettings(BaseSettings):
    """对象存储配置"""
    default_type: str = Field(default="minio", description="默认存储类型")
    https: bool = Field(default=False, description="是否使用 HTTPS")
    bucket: str = Field(default="", description="默认存储桶名称")
    minio: MinioSettings = Field(default_factory=MinioSettings, description="MinIO 配置")
    aliyun: AliyunOssSettings = Field(
        default_factory=AliyunOssSettings, description="阿里云 OSS 配置"
    )
    tencent: TencentCosSettings = Field(
        default_factory=TencentCosSettings, description="腾讯云 COS 配置"
    )


class MessagingPubSubSettings(BaseSettings):
    """发布订阅配置"""
    use: str = Field(default="redis", description="使用的类型: redis/rabbitmq")


class MessagingQueueSettings(BaseSettings):
    """队列配置"""
    use: str = Field(default="redis", description="使用的类型: redis/rabbitmq")


class MessagingSettings(BaseSettings):
    """消息队列配置"""
    connections: dict[str, Any] = Field(
        default_factory=dict, description="连接配置"
    )
    pubsub: MessagingPubSubSettings = Field(
        default_factory=MessagingPubSubSettings, description="发布订阅配置"
    )
    queue: MessagingQueueSettings = Field(
        default_factory=MessagingQueueSettings, description="队列配置"
    )


class LockSettings(BaseSettings):
    """锁配置"""
    provider: str = Field(default="redis", description="锁提供者: redis/sqlalchemy")


# ==============================================================================
# Web 配置
# ==============================================================================

class ServerSettings(BaseSettings):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8080, description="服务器端口")
    workers: int = Field(default=1, description="工作进程数")


class ApiDocsSettings(BaseSettings):
    """API 文档配置"""
    enabled: bool = Field(default=True, description="是否启用 API 文档")


class LoggingSettings(BaseSettings):
    """日志配置"""
    level: str = Field(default="info", description="日志级别")


# ==============================================================================
# 业务配置
# ==============================================================================

class TenantSettings(BaseSettings):
    """租户配置"""
    request_header: str = Field(default="x-tenant-id", description="租户请求头")
    default_tenant_id: str = Field(
        default="00000000-0000-0000-0000-000000000000", description="默认租户 ID"
    )
    default_workspace_id: str = Field(
        default="", description="默认工作空间 ID"
    )


class JWTSettings(BaseSettings):
    """JWT 配置"""
    secret_key: str = Field(
        default="change-me-in-production", description="JWT 签名密钥"
    )
    access_token_expire_hours: int = Field(
        default=2, description="Access Token 有效期（小时）"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh Token 有效期（天）"
    )
    algorithm: str = Field(
        default="HS256", description="JWT 签名算法"
    )


class OAuthWechatSettings(BaseSettings):
    """微信 OAuth 配置"""
    client_id: str = Field(default="", description="AppID")
    client_secret: str = Field(default="", description="AppSecret")
    redirect_uri: str = Field(default="", description="回调地址")


class OAuthWeworkSettings(BaseSettings):
    """企微 OAuth 配置"""
    client_id: str = Field(default="", description="CorpID")
    client_secret: str = Field(default="", description="CorpSecret")
    redirect_uri: str = Field(default="", description="回调地址")
    agentid: str = Field(default="", description="AgentID")


class OAuthSettings(BaseSettings):
    """OAuth 配置"""
    wechat: OAuthWechatSettings = Field(
        default_factory=OAuthWechatSettings, description="微信配置"
    )
    wework: OAuthWeworkSettings = Field(
        default_factory=OAuthWeworkSettings, description="企微配置"
    )


class IAMSettings(BaseSettings):
    """IAM 模块配置"""
    jwt: JWTSettings = Field(default_factory=JWTSettings, description="JWT 配置")
    oauth: OAuthSettings = Field(default_factory=OAuthSettings, description="OAuth 配置")


# ==============================================================================
# 主配置类
# ==============================================================================

class Settings(BaseSettings):
    """主配置类"""

    # 基础配置
    server: ServerSettings = Field(
        default_factory=ServerSettings, description="服务器配置"
    )
    api_docs: ApiDocsSettings = Field(
        default_factory=ApiDocsSettings, description="API 文档配置"
    )

    # 基础设施配置
    sqlalchemy: SqlalchemySettings = Field(
        default_factory=SqlalchemySettings, description="数据库配置"
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings, description="Redis 配置"
    )
    oss: OssSettings = Field(
        default_factory=OssSettings, description="对象存储配置"
    )
    messaging: MessagingSettings = Field(
        default_factory=MessagingSettings, description="消息队列配置"
    )
    lock: LockSettings = Field(
        default_factory=LockSettings, description="锁配置"
    )

    # 业务配置
    tenant: TenantSettings = Field(
        default_factory=TenantSettings, description="租户配置"
    )
    iam: IAMSettings = Field(
        default_factory=IAMSettings, description="IAM 配置"
    )

    # 日志配置
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings, description="日志配置"
    )


# ==============================================================================
# 全局配置实例
# ==============================================================================

_config_dir: Path | None = None
_settings: Settings | None = None


def init_settings(config_dir: Path | str) -> Settings:
    """
    初始化全局配置

    Args:
        config_dir: 配置文件目录

    Returns:
        Settings: 配置实例
    """
    global _settings, _config_dir

    _config_dir = Path(config_dir) if isinstance(config_dir, str) else config_dir

    from framework.configs.yaml import YamlParser
    parser = YamlParser(config_dir=_config_dir, base_config_file="application.yml")
    _settings = Settings.from_dict(parser.config_content or {})

    return _settings


def get_settings() -> Settings:
    """
    获取全局配置实例

    Returns:
        Settings: 配置实例

    Raises:
        RuntimeError: 如果配置未初始化
    """
    global _settings

    if _settings is None:
        raise RuntimeError("配置未初始化，请先调用 init_settings()")

    return _settings


# 为了向后兼容，提供 settings 属性访问
@property
def settings() -> Settings:
    """获取配置实例"""
    return get_settings()
