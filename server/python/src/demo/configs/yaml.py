"""
YAML 配置文件解析器
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from demo.core.common.env import ENV
from demo.utils.dictionary_util import deep_merge_dict

VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")
_path_to_env_cache: dict[str, str] = {}


class YamlParser:
    """
    配置文件解析器
    支持按顺序加载配置文件：
    1. application.{yaml|yml} - 基础配置
    2. application-common.{yaml|yml} - 公共配置
    3. application-{env}.{yaml|yml} - 环境特定配置

    支持环境变量覆盖配置值
    """

    def __init__(
        self,
        config_dir: Path | str,
        base_config_file: str = "application.yml",
    ):
        self.env = ENV
        self.config_dir = (
            Path(config_dir) if isinstance(config_dir, str) else config_dir
        )
        self.base_config_file = base_config_file
        self.config_content: dict[str, Any] | None = None
        self.load_file()

    def load_file(self) -> None:
        """按顺序加载配置文件并合并"""
        base_config_filename, ext = os.path.splitext(self.base_config_file)
        supported_extensions = [".yml", ".yaml"]
        if ext not in supported_extensions:
            ext = ".yml"

        config_files = [
            f"{base_config_filename}{ext}",
            f"{base_config_filename}-common{ext}",
            f"{base_config_filename}-{self.env}{ext}",
        ]

        merged_config: dict[str, Any] = {}

        for config_file in config_files:
            config_path = self.config_dir / config_file

            if config_path.exists():
                try:
                    with open(config_path, encoding="utf-8") as f:
                        file_config = yaml.safe_load(f)

                    if file_config:
                        merged_config = deep_merge_dict(merged_config, file_config)
                        print(f"已加载配置文件: {config_file}")
                except Exception as e:
                    raise OSError(f"配置文件读取失败，路径: {config_path}") from e

        if not merged_config:
            raise OSError(f"未找到任何有效的配置文件，请检查 {self.config_dir} 目录")

        # 应用环境变量覆盖
        final_config = self._apply_env_overrides(merged_config)
        self.config_content = final_config

    def _apply_env_overrides(
        self, config: dict[str, Any], path_prefix: str = ""
    ) -> dict[str, Any]:
        """应用环境变量覆盖配置值"""
        result = {}
        for key, value in config.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key
            env_var_name = self._convert_path_to_env_var(current_path)
            env_value = self._get_env_variable(env_var_name)

            if env_value is not None:
                result[key] = env_value
            elif isinstance(value, dict):
                result[key] = self._apply_env_overrides(value, current_path)
            else:
                result[key] = value

        return result

    def _convert_path_to_env_var(self, config_path: str) -> str:
        """将配置路径转换为环境变量名"""
        if config_path in _path_to_env_cache:
            return _path_to_env_cache[config_path]
        env_var_name = config_path.replace(".", "_").replace("-", "_").upper()
        _path_to_env_cache[config_path] = env_var_name
        return env_var_name

    @staticmethod
    def _convert_env_value_type(value: str) -> Any:
        """将环境变量字符串值转换为适当的类型"""
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return value
        if value.lower() in ("true", "yes", "on", "1"):
            return True
        elif value.lower() in ("false", "no", "off", "0"):
            return False
        try:
            if "." not in value and "e" not in value.lower():
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        return value

    @staticmethod
    def _get_env_variable(var_name: str) -> Any | None:
        """获取环境变量值"""
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return YamlParser._convert_env_value_type(env_value)
        return None

    def get_value(self, path: list[str], default: Any | None = None) -> Any:
        """获取配置文件中的值"""
        if self.config_content is None:
            raise OSError("配置文件未加载")

        try:
            value = self.config_content
            for key in path:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        except Exception:
            return default
