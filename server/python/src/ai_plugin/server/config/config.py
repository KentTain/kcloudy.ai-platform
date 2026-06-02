from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InstallMethod(Enum):
    """
    安装方式枚举类

    定义插件的安装和运行方式
    """

    Local = "local"  # 本地安装
    Remote = "remote"  # 远程安装
    Serverless = "serverless"  # 无服务器模式


class AlonPluginEnv(BaseSettings):
    """
    AlonPlugin环境配置类

    定义插件的环境配置参数，支持从环境变量和.env文件读取
    """

    MAX_REQUEST_TIMEOUT: int = Field(default=300, description="最大请求超时时间（秒）")
    MAX_WORKER: int = Field(
        default=1000,
        description="最大工作者数量，使用gevent进行异步IO，无需担心线程数量",
    )
    HEARTBEAT_INTERVAL: float = Field(default=10, description="心跳间隔时间（秒）")
    INSTALL_METHOD: InstallMethod = Field(
        default=InstallMethod.Local,
        description="安装方式，本地或网络",
    )

    # 远程安装相关配置
    REMOTE_INSTALL_URL: str | None = Field(default=None, description="远程安装URL")
    REMOTE_INSTALL_HOST: str = Field(default="localhost", description="远程安装主机")
    REMOTE_INSTALL_PORT: int = Field(default=5003, description="远程安装端口")
    REMOTE_INSTALL_KEY: str | None = Field(default=None, description="远程安装密钥")

    # 无服务器模式相关配置
    SERVERLESS_HOST: str = Field(default="0.0.0.0", description="无服务器模式主机")
    SERVERLESS_PORT: int = Field(default=8080, description="无服务器模式端口")
    SERVERLESS_WORKER_CLASS: str = Field(
        default="gevent", description="无服务器模式工作者类"
    )
    SERVERLESS_WORKER_CONNECTIONS: int = Field(
        default=1000, description="无服务器模式工作者连接数"
    )
    SERVERLESS_WORKERS: int = Field(default=5, description="无服务器模式工作者数量")
    SERVERLESS_THREADS: int = Field(default=5, description="无服务器模式线程数")

    # Dify插件守护进程URL
    DIFY_PLUGIN_DAEMON_URL: str = Field(
        default="http://localhost:5002", description="反向调用地址"
    )

    model_config = SettingsConfigDict(
        # 从dotenv格式配置文件读取
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        # 忽略额外属性
        extra="ignore",
    )
