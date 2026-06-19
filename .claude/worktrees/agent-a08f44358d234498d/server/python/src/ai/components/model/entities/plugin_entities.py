from datetime import datetime

from pydantic import BaseModel, Field

from ai_plugin.sdk.entities.model.provider import ProviderEntity


class PluginModelProviderEntity(BaseModel):
    """
    插件模型提供者实体类

    表示由插件提供的AI模型服务的完整信息
    """

    id: str = Field(description="唯一标识符")
    created_at: datetime = Field(description="模型提供者的创建时间")
    updated_at: datetime = Field(description="模型提供者的更新时间")
    provider: str = Field(description="模型提供者名称")
    tenant_id: str = Field(description="租户ID")
    plugin_unique_identifier: str = Field(description="插件唯一标识符")
    plugin_id: str = Field(description="插件ID")
    declaration: ProviderEntity = Field(description="模型提供者的声明配置")
