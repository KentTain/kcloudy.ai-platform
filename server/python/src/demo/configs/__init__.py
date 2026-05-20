"""
配置管理模块

从 framework.config 导入基础组件，提供 demo 特有的配置。
"""

from framework.config.base import BaseSettings
from framework.config.yaml import YamlParser
from framework.config.helpers import (
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
