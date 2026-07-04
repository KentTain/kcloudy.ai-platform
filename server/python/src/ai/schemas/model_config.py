"""模型配置 Schema"""

from __future__ import annotations

from framework.schemas import BaseModel


class ModelConfigItemResponse(BaseModel):
    """模型配置项响应"""

    model_name: str
    model_label: str | None = None
    model_type: str
    is_default: bool = False


class PluginWithModelsResponse(BaseModel):
    """插件及其模型列表响应"""

    plugin_id: str
    plugin_name: str
    status: str
    models: list[ModelConfigItemResponse] = []


class DefaultModelItemResponse(BaseModel):
    """默认模型展示项响应"""

    model_type: str
    plugin_id: str | None = None
    model_name: str | None = None
    is_valid: bool = True


class ModelConfigOverviewResponse(BaseModel):
    """模型配置页面聚合响应"""

    total_plugins: int = 0
    configured_plugins: int = 0
    total_models: int = 0
    default_models: list[DefaultModelItemResponse] = []
    plugins: list[PluginWithModelsResponse] = []


class AvailableModelItemResponse(BaseModel):
    """插件可用模型项响应"""

    model_name: str
    model_label: str | None = None
    model_type: str
    is_enabled: bool = False


class PluginAvailableModelsResponse(BaseModel):
    """插件可用模型列表响应"""

    models: list[AvailableModelItemResponse] = []


class ModelSelectItemResponse(BaseModel):
    """默认模型选择项响应"""

    plugin_id: str
    plugin_name: str
    provider: str
    model_name: str
    model_label: str | None = None
    model_type: str


class ModelSelectListResponse(BaseModel):
    """默认模型选择列表响应"""

    models: list[ModelSelectItemResponse] = []


class DefaultModelItemRequest(BaseModel):
    """批量设置默认模型项请求"""

    model_type: str
    plugin_id: str
    model_name: str | None = None


class BatchSetDefaultModelRequest(BaseModel):
    """批量设置默认模型请求"""

    items: list[DefaultModelItemRequest]


class EnabledModelsRequest(BaseModel):
    """配置启用模型请求"""

    model_names: list[str]
