"""
统一配置模块

基于 YAML 文件的配置加载，支持：
- 分层配置加载
- 环境变量覆盖
- Pydantic 验证
"""

from framework.configs.base import BaseSettings
from framework.configs.helpers import (
    convert_dict_hyphen_to_underscore,
    hyphen_to_underscore,
)
from framework.configs.settings import (
    Settings,
    get_settings,
    init_settings,
)
from framework.configs.yaml import YamlParser

__all__ = [
    "BaseSettings",
    "YamlParser",
    "hyphen_to_underscore",
    "convert_dict_hyphen_to_underscore",
    "Settings",
    "init_settings",
    "get_settings",
]
