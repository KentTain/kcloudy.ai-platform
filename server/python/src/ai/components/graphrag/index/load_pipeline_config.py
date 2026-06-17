"""包含read_dotenv,load_pipeline_config,_parse_yaml和_create_include_constructor方法定义的模块."""

import json
from pathlib import Path

import yaml
from pyaml_env import parse_config as parse_config_with_env

from ai.components.graphrag.config import create_graphrag_config, read_dotenv
from ai.components.graphrag.index.config import PipelineConfig
from ai.components.graphrag.index.create_pipeline_config import create_pipeline_config


def load_pipeline_config(config_or_path: str | PipelineConfig) -> PipelineConfig:
    """从文件路径或配置对象加载流水线配置."""
    if isinstance(config_or_path, PipelineConfig):
        config = config_or_path
    elif config_or_path == "default":
        config = create_pipeline_config(create_graphrag_config(root_dir="."))
    else:
        # 配置所在目录中是否有.env文件?
        read_dotenv(str(Path(config_or_path).parent))

        if config_or_path.endswith(".json"):
            with Path(config_or_path).open("rb") as f:
                config = json.loads(f.read().decode(encoding="utf-8", errors="strict"))
        elif config_or_path.endswith((".yml", ".yaml")):
            config = _parse_yaml(config_or_path)
        else:
            msg = f"Invalid config file type: {config_or_path}"
            raise ValueError(msg)

        config = PipelineConfig.model_validate(config)
        if not config.root_dir:
            config.root_dir = str(Path(config_or_path).parent.resolve())

    if config.extends is not None:
        if isinstance(config.extends, str):
            config.extends = [config.extends]
        for extended_config in config.extends:
            extended_config = load_pipeline_config(extended_config)
            merged_config = {
                **json.loads(extended_config.model_dump_json()),
                **json.loads(config.model_dump_json(exclude_unset=True)),
            }
            config = PipelineConfig.model_validate(merged_config)

    return config


def _parse_yaml(path: str):
    """解析yaml文件,支持!include指令."""
    # 我不喜欢这是静态的
    loader_class = yaml.SafeLoader

    # 如果尚未存在,添加!include构造器。
    if "!include" not in loader_class.yaml_constructors:
        loader_class.add_constructor("!include", _create_include_constructor())

    return parse_config_with_env(path, loader=loader_class, default_value="")


def _create_include_constructor():
    """为!include指令创建构造器."""

    def handle_include(loader: yaml.Loader, node: yaml.Node):
        """包含节点引用的文件."""
        filename = str(Path(loader.name).parent / node.value)
        if filename.endswith((".yml", ".yaml")):
            return _parse_yaml(filename)

        with Path(filename).open("rb") as f:
            return f.read().decode(encoding="utf-8", errors="strict")

    return handle_include
