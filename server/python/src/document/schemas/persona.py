"""人设 Schema"""

from datetime import datetime

from pydantic import Field

from framework.schemas import BaseModel, BasePaginatedQuery


class PersonaCreate(BaseModel):
    """创建人设请求"""

    name: str = Field(..., description="人设名称")
    instruction: str = Field(..., description="提示词")
    role: str | None = Field(default=None, description="角色")
    description: str | None = Field(default=None, description="描述")


class PersonaUpdate(BaseModel):
    """更新人设请求"""

    name: str | None = Field(default=None, description="人设名称")
    instruction: str | None = Field(default=None, description="提示词")
    role: str | None = Field(default=None, description="角色")
    description: str | None = Field(default=None, description="描述")


class PersonaPaginatedQuery(BasePaginatedQuery):
    """人设分页查询"""

    pass


class PersonaResponse(BaseModel):
    """人设响应"""

    id: str
    name: str
    instruction: str
    role: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class PersonaOptionResponse(BaseModel):
    """人设选项响应（下拉选择用）"""

    id: str
    name: str
    role: str | None = None
    description: str | None = None
