"""
配置基类

提供基于 Pydantic 的配置验证功能。
"""

from typing import Any, TypeVar

from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

from framework.configs.helpers import convert_dict_hyphen_to_underscore

T = TypeVar("T", bound="BaseSettings")


class BaseSettings(PydanticBaseSettings):
    """基础配置类，继承自 PydanticBaseSettings"""

    model_config = SettingsConfigDict(
        extra="ignore",
    )

    @classmethod
    def from_dict(cls: type[T], config_dict: dict[str, Any]) -> T:
        """
        从字典中加载配置数据并创建配置实例

        此方法将 YAML 配置文件解析后的字典转换为类型安全的配置对象。
        支持将连字符命名的配置键转换为下划线命名。

        Args:
            config_dict: 包含配置数据的字典，通常来自 YAML 配置文件

        Returns:
            T: 验证后的配置对象实例（实际调用该方法的子类类型）

        Raises:
            ValueError: 当配置字典为空时
            ValidationError: 当配置数据不符合 Pydantic 模型定义时
        """
        if len(config_dict) == 0:
            raise ValueError("配置字典不能为空")

        # 先将连字符转下划线（YAML 配置文件中常用连字符命名）
        converted_dict = convert_dict_hyphen_to_underscore(config_dict)

        # 使用 Pydantic 模型验证方法创建实例
        try:
            return cls.model_validate(converted_dict)
        except Exception as e:
            # 打印详细错误信息，帮助调试
            import sys

            print(f"配置验证错误: {e}", file=sys.stderr)
            print(f"配置内容: {converted_dict}", file=sys.stderr)
            raise e
