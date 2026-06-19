"""
模型组件配置模块
"""

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """模型组件配置"""

    # 插件守护进程配置
    PLUGIN_DAEMON_URL: str = Field(default="")
    PLUGIN_DAEMON_KEY: str = Field(default="")

    # 安全配置
    SECRET_KEY: str = Field(default="")

    # 文件服务配置
    FILES_URL: str = Field(default="")
    FILES_ACCESS_TIMEOUT: int = Field(default=0)

    # Token 计数配置
    PLUGIN_BASED_TOKEN_COUNTING_ENABLED: bool = Field(default=False)

    # 调试模式
    DEBUG: bool = Field(default=False)

    # 位置配置
    POSITION_TOOL_INCLUDES_SET: set[str] = Field(default_factory=set)
    POSITION_TOOL_EXCLUDES_SET: set[str] = Field(default_factory=set)
    POSITION_PROVIDER_INCLUDES_SET: set[str] = Field(default_factory=set)
    POSITION_PROVIDER_EXCLUDES_SET: set[str] = Field(default_factory=set)
    POSITION_TOOL_PINS_LIST: list[str] = Field(default_factory=list)
    POSITION_PROVIDER_PINS_LIST: list[str] = Field(default_factory=list)

    # 代码执行配置
    CODE_EXECUTION_ENDPOINT: str = Field(default="")
    CODE_EXECUTION_API_KEY: str = Field(default="")
    CODE_EXECUTION_CONNECT_TIMEOUT: int = Field(default=0)
    CODE_EXECUTION_READ_TIMEOUT: int = Field(default=0)
    CODE_EXECUTION_WRITE_TIMEOUT: int = Field(default=0)

    # SSRF 防护配置
    SSRF_DEFAULT_MAX_RETRIES: int = Field(default=3)
    HTTP_REQUEST_NODE_SSL_VERIFY: bool = Field(default=True)
    SSRF_DEFAULT_TIME_OUT: int = Field(default=60)
    SSRF_DEFAULT_CONNECT_TIME_OUT: int = Field(default=10)
    SSRF_DEFAULT_READ_TIME_OUT: int = Field(default=60)
    SSRF_DEFAULT_WRITE_TIME_OUT: int = Field(default=60)
    SSRF_PROXY_ALL_URL: str = Field(default="")
    SSRF_PROXY_HTTP_URL: str = Field(default="")
    SSRF_PROXY_HTTPS_URL: str = Field(default="")


# 全局配置实例
model_config = ModelConfig()
