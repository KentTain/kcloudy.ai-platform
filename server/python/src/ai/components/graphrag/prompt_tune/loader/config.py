"""配置加载,解析和处理模块。

Config loading, parsing and handling module.
"""

from pathlib import Path

from ai.components.graphrag.config import create_graphrag_config
from ai.components.graphrag.index.progress.types import ProgressReporter


def read_config_parameters(
    root: str, reporter: ProgressReporter, config: str | None = None
):
    """
    从设置文件或环境变量读取配置参数。

    依次尝试从 YAML 文件,JSON 文件读取配置,如果都不存在则从环境变量读取。

    Read the configuration parameters from the settings file or environment variables.

    参数 Parameters
    ----------
    - root: 参数所在的根目录。The root directory where the parameters are.
    - reporter: 进度报告器。The progress reporter.
    - config: 设置文件的路径(可选)。The path to the settings file.
    """
    _root = Path(root)

    # 尝试读取 YAML 配置文件
    # Try to read YAML config file
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"
    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("rb") as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    # 尝试读取 JSON 配置文件
    # Try to read JSON config file
    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings.json"
    )
    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("rb") as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    if settings_json.exists():
        reporter.info(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    # 从环境变量读取设置
    # Read settings from environment variables
    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
