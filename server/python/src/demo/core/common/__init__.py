"""
核心公共模块
"""

from demo.core.common.env import ENV
from demo.core.common.instance import get_instance_id, set_instance_id
from demo.core.common.path import (
    CONFIG_FOLDER,
    LOGS_DIR,
    ROOT_DIR,
    SRC_DIR,
    WORKSPACE_ROOT_DIR,
)
from demo.core.common.singleton import AbstractSingleton, Singleton
from demo.core.common.time import ChinaTimeZone

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
