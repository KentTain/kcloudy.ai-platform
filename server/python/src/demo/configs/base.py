"""
基础配置类
"""

from typing import Any, TypeVar

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

from demo.configs.helpers import convert_dict_hyphen_to_underscore

T = TypeVar("T", bound="BaseSettings")


class BaseSettings(PydanticBaseSettings):
    """基础配置类"""

    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def from_dict(cls: type[T], config_dict: dict[str, Any]) -> T:
        """从字典中加载配置数据并创建配置实例"""
        if len(config_dict) == 0:
            raise ValueError("配置字典不能为空")
        converted_dict = convert_dict_hyphen_to_underscore(config_dict)
        return cls.model_validate(converted_dict)

    def to_dict(self) -> dict[str, Any]:
        """将配置实例转换为字典"""
        return self.model_dump()
