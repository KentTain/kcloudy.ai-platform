"""
配置管理模块

从 framework.config 模块导入。
"""

# 从 framework 导入配置组件
from framework.config.base import BaseSettings
from framework.config.yaml import YamlParser
from framework.config.settings import (
    Settings,
    init_settings,
    get_settings,
)

# 兼容旧代码
settings = None
config = None


def init_demo_settings(config_dir: str):
    """
    初始化 demo 模块配置

    Args:
        config_dir: 配置文件目录
    """
    global settings, config

    from pathlib import Path
    config_path = Path(config_dir)
    config = YamlParser(config_dir=config_path, base_config_file="application.yml")
    settings = Settings.from_dict(config.config_content or {})

    return settings


__all__ = [
    "BaseSettings",
    "YamlParser",
    "Settings",
    "init_settings",
    "get_settings",
    "init_demo_settings",
    "settings",
    "config",
]
