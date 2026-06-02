from pydantic import BaseModel, Field, field_validator

from ai_plugin.sdk.entities.provider_config import ProviderConfig
from ai_plugin.server.core.documentation.schema_doc import docs
from ai_plugin.server.core.utils.yaml_loader import load_yaml_file


@docs(
    name="EndpointExtra",
    description="端点额外配置",
)
class EndpointConfigurationExtra(BaseModel):
    """
    端点配置额外信息模型类

    存储端点的额外配置信息，如Python源码等
    """

    class Python(BaseModel):
        """
        Python配置子类

        存储Python相关的配置信息
        """

        source: str  # Python源码路径或内容

    python: Python  # Python配置


@docs(
    name="Endpoint",
    description="端点配置清单",
)
class EndpointConfiguration(BaseModel):
    """
    端点配置模型类

    定义单个端点的配置信息，包括路径、方法、是否隐藏等
    """

    path: str  # 端点路径
    method: str  # HTTP方法
    hidden: bool = Field(default=False, description="是否在UI中隐藏此端点")
    extra: EndpointConfigurationExtra  # 额外配置信息


@docs(
    name="EndpointGroup",
    description="端点组配置清单",
    outside_reference_fields={"endpoints": EndpointConfiguration},
)
class EndpointProviderConfiguration(BaseModel):
    """
    端点提供者配置模型类

    定义端点提供者的完整配置，包括设置和端点列表
    """

    settings: list[ProviderConfig] = Field(default_factory=list)  # 设置配置列表
    endpoints: list[EndpointConfiguration] = Field(default_factory=list)  # 端点配置列表

    @classmethod
    def _load_yaml_file(cls, path: str) -> dict:
        """
        加载YAML配置文件

        Args:
            path: YAML文件路径

        Returns:
            dict: 解析后的配置字典
        """
        return load_yaml_file(path)

    @field_validator("endpoints", mode="before")
    @classmethod
    def validate_endpoints(cls, value) -> list[EndpointConfiguration]:
        """
        验证端点配置列表

        支持从YAML文件加载端点配置或直接使用配置对象

        Args:
            value: 端点配置值，可以是列表、字典或文件路径

        Returns:
            list[EndpointConfiguration]: 验证后的端点配置列表

        Raises:
            ValueError: 当配置格式无效时抛出
        """
        if not isinstance(value, list):
            raise ValueError("端点配置应该是一个列表")

        endpoints: list[EndpointConfiguration] = []

        for endpoint in value:
            # 从YAML读取或直接加载
            if isinstance(endpoint, EndpointConfiguration | dict):
                if isinstance(endpoint, dict):
                    endpoint = EndpointConfiguration(**endpoint)
                endpoints.append(endpoint)
                continue

            if not isinstance(endpoint, str):
                raise ValueError("端点路径应该是字符串")

            try:
                # 从YAML文件加载配置
                file = cls._load_yaml_file(endpoint)
                endpoints.append(EndpointConfiguration(**file))
            except Exception as e:
                raise ValueError(f"加载端点配置时出错: {e!s}") from e

        return endpoints
