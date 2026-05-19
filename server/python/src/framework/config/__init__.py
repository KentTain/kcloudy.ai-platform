"""
统一配置模块

基于 YAML 文件的配置加载，支持：
- 分层配置加载
- 环境变量覆盖
- Pydantic 验证
"""

from framework.config.base import BaseSettings
from framework.config.yaml import YamlParser
from framework.config.helpers import (
    hyphen_to_underscore,
    convert_dict_hyphen_to_underscore,
)
from framework.config.settings import (
    Settings,
    init_settings,
    get_settings,
)

__all__ = [
    "BaseSettings",
    "YamlParser",
    "hyphen_to_underscore",
    "convert_dict_hyphen_to_underscore",
    "Settings",
    "init_settings",
    "get_settings",
]
