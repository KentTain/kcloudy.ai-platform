"""模型列表 Schema

定义模型列表接口的响应 Schema。
"""

from pydantic import BaseModel, Field


class ModelItem(BaseModel):
    """模型项 Schema"""

    id: str = Field(description="模型 ID，格式为 provider/model")
    name: str = Field(description="模型名称")
    description: str | None = Field(default=None, description="模型描述")


class ProviderItem(BaseModel):
    """提供商项 Schema"""

    id: str = Field(description="提供商 ID")
    name: str = Field(description="提供商显示名称")
    models: list[ModelItem] = Field(default_factory=list, description="模型列表")


class ModelListResponse(BaseModel):
    """模型列表响应 Schema"""

    providers: list[ProviderItem] = Field(default_factory=list, description="提供商列表")
