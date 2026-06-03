from typing import Any

from pydantic import BaseModel, Field

from ai_plugin.sdk.entities.provider_config import CommonParameterType


class ParameterEntity(BaseModel):
    """参数实体"""

    name: str = Field(description="参数名称")
    type: CommonParameterType = Field(description="参数类型")
    label: str = Field(description="参数标签")
    description: str | None = Field(default=None, description="参数描述")
    required: bool = Field(default=False, description="是否必需")
    default: Any | None = Field(default=None, description="默认值")
    placeholder: str | None = Field(default=None, description="占位符")
    options: list[dict[str, Any]] | None = Field(default=None, description="选项列表")
    min_value: int | float | None = Field(default=None, description="最小值")
    max_value: int | float | None = Field(default=None, description="最大值")
    min_length: int | None = Field(default=None, description="最小长度")
    max_length: int | None = Field(default=None, description="最大长度")
    pattern: str | None = Field(default=None, description="正则表达式模式")


class ParameterGroup(BaseModel):
    """参数组"""

    name: str = Field(description="组名称")
    label: str = Field(description="组标签")
    description: str | None = Field(default=None, description="组描述")
    parameters: list[ParameterEntity] = Field(default=[], description="参数列表")
    collapsible: bool = Field(default=False, description="是否可折叠")
    collapsed: bool = Field(default=False, description="是否默认折叠")


class FormSchema(BaseModel):
    """表单模式"""

    title: str = Field(description="表单标题")
    description: str | None = Field(default=None, description="表单描述")
    groups: list[ParameterGroup] = Field(default=[], description="参数组列表")
    submit_text: str | None = Field(default="提交", description="提交按钮文本")
    cancel_text: str | None = Field(default="取消", description="取消按钮文本")


class ValidationRule(BaseModel):
    """验证规则"""

    type: str = Field(description="验证类型")
    message: str = Field(description="错误消息")
    value: Any | None = Field(default=None, description="验证值")


class ParameterConfig(BaseModel):
    """参数配置"""

    parameter: ParameterEntity = Field(description="参数定义")
    validation_rules: list[ValidationRule] = Field(default=[], description="验证规则")
    dependencies: list[str] = Field(default=[], description="依赖参数")
    conditional_display: dict[str, Any] | None = Field(
        default=None, description="条件显示配置"
    )
