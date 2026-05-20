"""
YAML 配置文件解析器（代理模式）

继承 framework 的 YamlParser，使用 demo 的环境变量命名。
"""

from pathlib import Path
from typing import Any

from framework.configs.yaml import YamlParser as FrameworkYamlParser


class YamlParser(FrameworkYamlParser):
    """
    Demo 专用的 YAML 解析器

    继承 framework 的 YamlParser，使用 demo 的环境变量命名（PYTHON_SERVICE_ENV）。
    """

    def __init__(
        self,
        config_dir: Path | str,
        base_config_file: str = "application.yml",
    ):
        # 使用 demo 的环境变量
        from demo.core.common.env import ENV
        super().__init__(config_dir, base_config_file, env=ENV)