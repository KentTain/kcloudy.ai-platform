"""
核心公共模块

从 framework 导入通用组件，保留 demo 特有的路径和环境配置。
"""

from demo.core.common.env import ENV
from demo.core.common.path import (
    CONFIG_FOLDER,
    LOGS_DIR,
    ROOT_DIR,
    SRC_DIR,
    WORKSPACE_ROOT_DIR,
)
from framework.common.instance import get_instance_id, set_instance_id
from framework.common.singleton import AbstractSingleton, Singleton
from framework.common.time import ChinaTimeZone

__all__ = [
    "ENV",
    "CONFIG_FOLDER",
    "LOGS_DIR",
    "ROOT_DIR",
    "SRC_DIR",
    "WORKSPACE_ROOT_DIR",
    "ChinaTimeZone",
    "Singleton",
    "AbstractSingleton",
    "get_instance_id",
    "set_instance_id",
]
