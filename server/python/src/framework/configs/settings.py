"""
全局配置定义

包含所有配置项的类型安全定义。
"""

from pathlib import Path
from typing import Any

from pydantic import Field

from framework.configs.base import BaseSettings
from framework.configs.encryption import EncryptionSettings

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
    auto_migrate: bool = Field(
        default=False,
        description="启动时自动运行数据库迁移（仅开发环境建议开启）"
    )
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
    bucket: str = Field(default="ai-platform", description="存储桶名称")


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
    minio: MinioSettings = Field(
        default_factory=MinioSettings, description="MinIO 配置"
    )
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

    connections: dict[str, Any] = Field(default_factory=dict, description="连接配置")
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


class WorkflowSettings(BaseSettings):
    """工作流配置"""

    task_cleanup_timeout: int = Field(default=600, description="任务超时清理时间（秒）")


class TenantSettings(BaseSettings):
    """租户配置"""

    request_header: str = Field(default="x-tenant-id", description="租户请求头")
    default_tenant_id: str = Field(
        default="00000000-0000-0000-0000-000000000000", description="默认租户 ID"
    )
    # 默认租户使用资源配置关联，不再使用内嵌配置
    default_db_config_id: str | None = Field(default=None, description="默认租户数据库配置ID")
    default_storage_config_id: str | None = Field(default=None, description="默认租户存储配置ID")
    default_cache_config_id: str | None = Field(default=None, description="默认租户缓存配置ID")
    default_queue_config_id: str | None = Field(default=None, description="默认租户队列配置ID")
    default_pubsub_config_id: str | None = Field(default=None, description="默认租户发布订阅配置ID")
    # 跳过租户中间件的路径前缀（支持个性化配置）
    skip_tenant_setting_path: list[str] = Field(
        default_factory=list, description="跳过租户中间件的路径前缀列表"
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
    algorithm: str = Field(default="HS256", description="JWT 签名算法")


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
    oauth: OAuthSettings = Field(
        default_factory=OAuthSettings, description="OAuth 配置"
    )


class InnerApiSettings(BaseSettings):
    """内部接口配置"""

    # 模块调用模式：monolith（单体直接调用）/ microservice（HTTP 调用）
    mode: str = Field(default="monolith", description="调用模式: monolith/microservice")

    # 各模块 inner 接口地址（microservice 模式下使用）
    tenant_url: str = Field(default="", description="Tenant 模块 inner 接口地址")
    iam_url: str = Field(default="", description="IAM 模块 inner 接口地址")

    # HTTP 客户端配置
    timeout: float = Field(default=30.0, description="请求超时时间（秒）")
    retry_count: int = Field(default=3, description="重试次数")


class PluginSettings(BaseSettings):
    """插件系统配置"""

    # 基础配置
    plugin_base_dir: str = Field(
        default="", description="插件工作目录基路径，为空则使用默认路径"
    )
    invocation_mode: str = Field(default="local", description="调用模式: local/remote")
    remote_plugin_base_url: str = Field(
        default="http://localhost:8080", description="远程插件服务地址"
    )
    remote_plugin_dispatch_path: str = Field(
        default="/api/v1/inner/plugin", description="远程插件调度路径"
    )
    expose_plugin_endpoints: bool = Field(default=True, description="是否暴露插件端点")

    # 启动时自动扫描插件目录
    scan_on_startup: bool = Field(
        default=False, description="启动时是否自动扫描插件目录"
    )
    scan_directory: str = Field(
        default="", description="启动时扫描的插件目录路径，为空则不扫描"
    )

    # 存储配置
    storage_bucket: str = Field(default="plugins", description="插件包存储桶名称")

    # 任务配置
    install_task_timeout_seconds: int = Field(
        default=1800, description="安装任务超时时间（秒），默认 30 分钟"
    )

    # 缓存配置
    runtime_state_cache_ttl: int = Field(
        default=60, description="运行时状态缓存 TTL（秒）"
    )

    # Python 环境
    python_version: str = Field(default="3.12", description="插件 Python 版本")
    uv_path: str | None = Field(default=None, description="uv 可执行文件路径")
    uv_python_install_mirror: str = Field(
        default="https://registry.npmmirror.com/-/binary/python-build-standalone/",
        description="Python 安装镜像",
    )
    pip_index_url: str = Field(
        default="https://mirrors.aliyun.com/pypi/simple/",
        description="pip 索引 URL",
    )
    pip_trusted_host: str | None = Field(default=None, description="pip 受信主机")
    allow_system_packages: bool = Field(default=False, description="是否允许使用系统包")

    # uv 配置
    uv_verbose: bool = Field(default=False, description="uv 详细输出")
    uv_cache_dir: str | None = Field(default=None, description="uv 缓存目录")
    uv_http_timeout: int = Field(default=300, description="uv HTTP 超时（秒）")
    uv_concurrent_downloads: int = Field(default=5, description="uv 并发下载数")
    uv_retry_attempts: int = Field(default=3, description="uv 重试次数")
    uv_venv_timeout: int = Field(default=180, description="uv 虚拟环境创建超时（秒）")

    # 插件运行时
    plugin_dependency_timeout: int = Field(
        default=180, description="插件依赖安装超时（秒）"
    )
    enable_precompile: bool = Field(default=False, description="是否启用预编译")
    strict_security_mode: bool = Field(
        default=False, description="是否启用严格安全模式"
    )

    # 自动冻结
    plugin_freeze_threshold_seconds: int = Field(
        default=1800, description="插件自动冻结阈值（秒），超过此时间未访问则自动停止"
    )

    # 插件预热
    enable_plugin_warmup: bool = Field(default=False, description="是否启用插件预热")
    plugin_warmup_list: list[str] = Field(
        default_factory=list, description="启动时预热的插件列表"
    )

    # 代理配置
    http_proxy: str | None = Field(default=None, description="HTTP 代理")
    https_proxy: str | None = Field(default=None, description="HTTPS 代理")
    no_proxy: str | None = Field(default=None, description="不使用代理的地址")


class CodeSandboxSettings(BaseSettings):
    """代码沙箱配置"""

    endpoint: str = Field(default="http://localhost:8194", description="代码沙箱端点")
    api_key: str = Field(default="", description="API密钥")
    connect_timeout: int = Field(default=10, description="连接超时时间（秒）")
    read_timeout: int = Field(default=60, description="读取超时时间（秒）")
    write_timeout: int = Field(default=60, description="写入超时时间（秒）")


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
    oss: OssSettings = Field(default_factory=OssSettings, description="对象存储配置")
    messaging: MessagingSettings = Field(
        default_factory=MessagingSettings, description="消息队列配置"
    )
    lock: LockSettings = Field(default_factory=LockSettings, description="锁配置")

    # 业务配置
    tenant: TenantSettings = Field(
        default_factory=TenantSettings, description="租户配置"
    )
    iam: IAMSettings = Field(default_factory=IAMSettings, description="IAM 配置")
    workflow: WorkflowSettings = Field(
        default_factory=WorkflowSettings, description="工作流配置"
    )

    # 内部接口配置
    inner_api: InnerApiSettings = Field(
        default_factory=InnerApiSettings, description="内部接口配置"
    )

    # 插件系统配置
    plugin: PluginSettings = Field(
        default_factory=PluginSettings, description="插件系统配置"
    )

    # 加密配置
    encryption: EncryptionSettings | None = Field(
        default=None, description="加密配置"
    )

    # 代码沙箱配置
    code_sandbox: CodeSandboxSettings = Field(
        default_factory=CodeSandboxSettings, description="代码沙箱配置"
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


def init_settings(
    config_dir: Path | str, parser_class: type[Any] | None = None
) -> Settings:
    """
    初始化全局配置

    Args:
        config_dir: 配置文件目录
        parser_class: 配置解析器类

    Returns:
        Settings: 配置实例
    """
    global _settings, _config_dir

    _config_dir = Path(config_dir) if isinstance(config_dir, str) else config_dir

    if parser_class is None:
        from framework.configs.yaml import YamlParser

        parser_class = YamlParser

    parser = parser_class(config_dir=_config_dir, base_config_file="application.yml")
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


settings = get_settings
