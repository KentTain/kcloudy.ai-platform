"""
配置管理模块

从 framework.configs 导入基础组件，提供 demo 特有的配置。
"""

from framework.configs.base import BaseSettings
from framework.configs.yaml import YamlParser
from framework.configs.helpers import (
    hyphen_to_underscore,
    convert_dict_hyphen_to_underscore,
)
from demo.configs.settings import Settings, settings, config

__all__ = [
    "BaseSettings",
    "YamlParser",
    "hyphen_to_underscore",
    "convert_dict_hyphen_to_underscore",
    "Settings",
    "settings",
    "config",
]
