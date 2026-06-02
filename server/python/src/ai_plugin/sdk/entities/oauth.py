from collections.abc import Sequence

from pydantic import BaseModel, Field

from ai_plugin.sdk.entities.provider_config import ProviderConfig
from ai_plugin.server.core.documentation.schema_doc import docs


@docs(
    name="OAuthSchema",
    description="OAuth认证架构",
)
class OAuthSchema(BaseModel):
    """
    OAuth认证架构模型类

    定义OAuth客户端和凭证的配置架构
    """

    client_schema: Sequence[ProviderConfig] = Field(
        default_factory=list, description="OAuth客户端的配置架构"
    )
    credentials_schema: Sequence[ProviderConfig] = Field(
        default_factory=list, description="OAuth凭证的配置架构"
    )
