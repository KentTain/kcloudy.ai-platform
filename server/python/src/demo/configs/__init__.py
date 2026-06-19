"""
配置管理模块

复用 framework 的配置系统，使用 demo 特有的环境变量 (PYTHON_SERVICE_ENV)。
"""

from demo.configs.yaml import YamlParser
from demo.core.common.path import CONFIG_FOLDER
from framework.configs.base import BaseSettings
from framework.configs.settings import Settings, init_settings

settings = init_settings(CONFIG_FOLDER, parser_class=YamlParser)
config = YamlParser(config_dir=CONFIG_FOLDER, base_config_file="application.yml")

__all__ = [
    "BaseSettings",
    "Settings",
    "settings",
    "config",
]
