"""
配置管理模块

复用 framework 的配置系统，使用 demo 特有的环境变量 (PYTHON_SERVICE_ENV)。
"""

from framework.configs.base import BaseSettings
from framework.configs.settings import Settings
from demo.configs.yaml import YamlParser
from demo.core.common.path import CONFIG_FOLDER

# 使用 demo 的 YamlParser 初始化配置（支持 PYTHON_SERVICE_ENV）
_parser = YamlParser(config_dir=CONFIG_FOLDER, base_config_file="application.yml")
settings = Settings.from_dict(_parser.config_content or {})
config = _parser

__all__ = [
    "BaseSettings",
    "Settings",
    "settings",
    "config",
]
