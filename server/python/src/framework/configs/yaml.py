"""
YAML 配置文件解析器

支持按顺序加载配置文件：
1. application.{yaml|yml} - 基础配置
2. application-common.{yaml|yml} - 公共配置
3. application-{env}.{yaml|yml} - 环境特定配置

支持环境变量覆盖配置值。
"""

import os
import re
from pathlib import Path
from typing import Any

from framework.configs.helpers import deep_merge_dict

VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")
"""变量引用正则表达式，匹配${xxx.yyy}格式"""

_path_to_env_cache: dict[str, str] = {}
"""配置路径到环境变量名的转换缓存"""


def get_env() -> str:
    """获取当前环境"""
    return os.environ.get("APP_ENV", "local")


class YamlParser:
    """
    配置文件解析器

    支持按顺序加载配置文件并合并，支持环境变量覆盖。
    """

    def __init__(
        self,
        config_dir: Path | str,
        base_config_file: str = "application.yml",
        env: str | None = None,
    ):
        self.env = env or get_env()
        self.config_dir = (
            Path(config_dir) if isinstance(config_dir, str) else config_dir
        )
        self.base_config_file = base_config_file

        self.config_content: dict[str, Any] | None = None

        self.load_file()

    def load_file(self):
        """按顺序加载配置文件并合并"""
        import yaml

        # 解析基础配置文件名和扩展名
        base_config_filename, ext = os.path.splitext(self.base_config_file)

        # 支持的配置文件扩展名
        supported_extensions = [".yml", ".yaml"]
        if ext not in supported_extensions:
            ext = ".yml"

        # 定义配置文件加载顺序
        config_files = [
            f"{base_config_filename}{ext}",
            f"{base_config_filename}-common{ext}",
            f"{base_config_filename}-{self.env}{ext}",
        ]

        merged_config = {}

        # 按顺序加载并合并配置文件
        for config_file in config_files:
            config_path = self.config_dir / config_file

            if config_path.exists():
                try:
                    with open(config_path, encoding="utf-8") as f:
                        file_config = yaml.safe_load(f)

                    if file_config:
                        merged_config = deep_merge_dict(merged_config, file_config)

                except Exception as e:
                    raise OSError(f"配置文件读取失败，路径: {config_path}: {e}")

        if not merged_config:
            raise OSError(f"未找到任何有效的配置文件，请检查 {self.config_dir} 目录")

        # 处理变量引用
        processed_config = self._process_variable_references(merged_config)

        # 应用环境变量覆盖
        final_config = self._apply_env_overrides(processed_config)

        self.config_content = final_config

    def _process_variable_references(self, config: Any, root_config: Any = None) -> Any:
        """递归处理配置中的变量引用"""
        if root_config is None:
            root_config = config

        if isinstance(config, dict):
            return {
                k: self._process_variable_references(v, root_config)
                for k, v in config.items()
            }
        elif isinstance(config, list):
            return [self._process_variable_references(item, root_config) for item in config]
        elif isinstance(config, str):
            return self._replace_variables(config, root_config)
        else:
            return config

    def _replace_variables(self, value: str, root_config: Any) -> Any:
        """替换字符串中的变量引用"""
        if not isinstance(value, str) or "${" not in value:
            return value

        matches = VAR_PATTERN.findall(value)
        if not matches:
            return value

        result = value
        for var_expression in matches:
            if ":" in var_expression:
                var_path, default_value = var_expression.split(":", 1)
            else:
                var_path = var_expression
                default_value = None

            var_value = self._resolve_variable(var_path, default_value, root_config)

            if value == f"${{{var_expression}}}":
                return var_value

            placeholder = f"${{{var_expression}}}"
            if placeholder in result and var_value is not None:
                result = result.replace(placeholder, str(var_value))

        return result

    def _resolve_variable(self, var_path: str, default_value: str | None, root_config: Any) -> Any:
        """解析变量引用"""
        # 优先尝试环境变量
        env_var_name = var_path.upper().replace(".", "_").replace("-", "_")
        env_value = os.environ.get(env_var_name)
        if env_value is not None:
            return self._convert_env_value_type(env_value)

        # 尝试从配置中获取
        if root_config is not None:
            try:
                path_parts = var_path.split(".")
                return self._get_value_from_config(root_config, path_parts)
            except (KeyError, TypeError):
                pass

        # 返回默认值
        if default_value is not None:
            return self._convert_env_value_type(default_value)

        return None

    def _get_value_from_config(self, config: dict[str, Any], path: list[str]) -> Any:
        """从配置字典中获取指定路径的值"""
        current = config
        for key in path:
            if isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"路径 {'.'.join(path)} 不存在")
                current = current[key]
            else:
                raise KeyError(f"路径 {key} 不是字典类型")
        return current

    def _apply_env_overrides(self, config: dict[str, Any], path_prefix: str = "") -> dict[str, Any]:
        """应用环境变量覆盖配置值"""
        result = {}
        for key, value in config.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key

            env_var_name = self._convert_path_to_env_var(current_path)
            env_value = os.environ.get(env_var_name)

            if env_value is not None:
                result[key] = self._convert_env_value_type(env_value)
            elif isinstance(value, dict):
                result[key] = self._apply_env_overrides(value, current_path)
            else:
                result[key] = value

        return result

    @staticmethod
    def _convert_path_to_env_var(config_path: str) -> str:
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

        # 布尔值转换
        if value.lower() in ("true", "yes", "on", "1"):
            return True
        elif value.lower() in ("false", "no", "off", "0"):
            return False

        # 数字转换
        try:
            if "." not in value and "e" not in value.lower():
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass

        return value

    def get_value(self, path: list[str], default: Any | None = None) -> Any:
        """获取配置文件中的值"""
        if self.config_content is None:
            raise OSError("配置文件未加载")

        try:
            return self._get_value_from_config(self.config_content, path)
        except KeyError:
            return default
