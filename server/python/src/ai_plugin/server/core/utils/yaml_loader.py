import logging
import os

import yaml

from ai_plugin.server.config.logger_format import plugin_logger_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


def load_yaml_file(file_path: str, ignore_error: bool = False) -> dict:
    """
    安全加载YAML文件为字典

    Args:
        file_path: YAML文件的路径
        ignore_error: 是否忽略错误
            如果为True，发生错误时返回空字典，并以警告级别记录错误
            如果为False，发生错误时抛出异常

    Returns:
        dict: YAML文件内容的字典表示
    """
    try:
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"加载YAML文件失败 {file_path}: 文件未找到")

        with open(file_path, encoding="utf-8") as file:
            try:
                return yaml.safe_load(file)
            except Exception as e:
                raise yaml.YAMLError(f"加载YAML文件失败 {file_path}: {e}") from e
    except FileNotFoundError as e:
        logger.debug(f"加载YAML文件失败 {file_path}: {e}")
        return {}
    except Exception as e:
        if ignore_error:
            logger.exception(f"加载YAML文件失败 {file_path}")
            return {}
        else:
            raise e
