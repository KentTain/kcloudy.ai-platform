"""
YAML 工具模块

迁移自 Alon: src/alon/components/model/internal/helper/yaml_utils.py
"""

from typing import Any

import yaml
from loguru import logger


def load_yaml_file(file_path: str, default_value: Any = None) -> Any:
    """
    加载 YAML 文件

    Args:
        file_path: YAML 文件路径
        default_value: 加载失败时的默认返回值

    Returns:
        YAML 文件内容，加载失败时返回 default_value
    """
    if default_value is None:
        default_value = []

    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or default_value
    except FileNotFoundError:
        logger.debug(f"YAML 文件不存在: {file_path}")
        return default_value
    except yaml.YAMLError as e:
        logger.warning(f"YAML 文件解析失败: {file_path}, {e}")
        return default_value
    except Exception as e:
        logger.error(f"加载 YAML 文件失败: {file_path}, {e}")
        return default_value
