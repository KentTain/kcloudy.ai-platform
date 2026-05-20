"""
Demo 业务配置

使用 framework 的 BaseSettings 作为基类，定义 demo 特有的配置结构。
"""

from pydantic import Field

from framework.config.base import BaseSettings
from demo.configs.yaml import YamlParser
from demo.core.common.path import CONFIG_FOLDER


class ServerSettings(BaseSettings):
    """服务器配置"""

    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")


class LoggingSettings(BaseSettings):
    """日志配置"""

    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="日志格式",
    )


class SqlalchemySettings(BaseSettings):
    """数据库配置"""

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/demo",
        description="数据库连接URL",
    )
    echo: bool = Field(default=False, description="是否打印SQL")
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")


class RedisSettings(BaseSettings):
    """Redis 配置"""

    url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")


class Settings(BaseSettings):
    """主配置类"""

    name: str = Field(default="demo", description="应用名称")
    server: ServerSettings = Field(
        default_factory=ServerSettings, description="服务器配置"
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings, description="日志配置"
    )
    sqlalchemy: SqlalchemySettings = Field(
        default_factory=SqlalchemySettings, description="数据库配置"
    )
    redis: RedisSettings = Field(default_factory=RedisSettings, description="Redis配置")


config = YamlParser(config_dir=CONFIG_FOLDER, base_config_file="application.yml")
settings = Settings.from_dict(config.config_content or {})
