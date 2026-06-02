from pydantic import BaseModel, Field, field_validator

from ai_plugin.sdk.entities import I18nObject


class PluginParameterOption(BaseModel):
    """
    插件参数选项类

    定义选择类型参数的可选项，包含值和本地化标签
    """

    value: str = Field(..., description="选项的值")
    label: I18nObject = Field(..., description="选项的本地化标签")

    @field_validator("value", mode="before")
    @classmethod
    def transform_id_to_str(cls, value) -> str:
        """
        将ID转换为字符串类型

        :param value: 待转换的值
        :return: 字符串类型的值
        """
        if not isinstance(value, str):
            return str(value)
        else:
            return value
