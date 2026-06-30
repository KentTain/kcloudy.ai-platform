"""插件默认模型配置 Schema"""

from __future__ import annotations

from framework.schemas import BaseModel


class PluginDefaultModelCreate(BaseModel):
    """创建默认模型请求"""

    model_type: str
    plugin_id: str
    model_name: str | None = None
    credential_id: str | None = None
    custom_base_url: str | None = None
    custom_model_name: str | None = None


class PluginDefaultModelResponse(BaseModel):
    """默认模型响应"""

    id: str
    tenant_id: str
    model_type: str
    plugin_id: str
    model_name: str | None = None
    credential_id: str | None = None
    custom_base_url: str | None = None
    custom_model_name: str | None = None
    is_valid: bool
