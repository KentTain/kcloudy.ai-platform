import glob
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

import yaml
from loguru import logger
from pydantic import BaseModel, Field

from ai.components.plugin.engine.models.schemas import PluginConfig
from ai_plugin.sdk.entities.agent import AgentStrategyProviderConfiguration
from ai_plugin.sdk.entities.model import AIModelEntity
from ai_plugin.sdk.entities.model.provider import ModelProviderConfiguration
from ai_plugin.sdk.entities.tool import ToolProviderConfiguration
from ai_plugin.server.core.entities.plugin.setup import (
    PluginAsset,
    PluginConfiguration,
)
from ai_plugin.server.core.utils.yaml_loader import load_yaml_file

# 获取模块级别的日志记录器
_logger = logger.bind(name=__name__)

# 泛型类型变量，用于配置类型
T = TypeVar("T", bound=BaseModel)


@dataclass
class ProviderConfigDefinition:
    """提供者配置定义

    定义每种配置类型的加载参数和属性提取逻辑
    """

    config_class: type[BaseModel]  # 配置类
    type_name: str  # 类型名称（用于日志）
    need_cwd_change: bool = False  # 是否需要切换工作目录
    provider_name_attrs: list[str] | None = None  # 提供者名称属性候选列表
    count_attrs: list[str] | None = None  # 计数属性列表（用于显示统计信息）

    def __post_init__(self):
        if self.provider_name_attrs is None:
            self.provider_name_attrs = ["provider", "name"]
        if self.count_attrs is None:
            self.count_attrs = ["models", "tools", "strategies"]


# 预定义的配置类型定义
PROVIDER_CONFIG_DEFINITIONS = {
    "tools": ProviderConfigDefinition(
        config_class=ToolProviderConfiguration,
        type_name="工具提供者",
        need_cwd_change=True,
        provider_name_attrs=["provider", "name"],
        count_attrs=["tools"],
    ),
    "models": ProviderConfigDefinition(
        config_class=ModelProviderConfiguration,
        type_name="模型提供者",
        need_cwd_change=True,
        provider_name_attrs=["provider", "name"],
        count_attrs=["models"],
    ),
    "agent_strategies": ProviderConfigDefinition(
        config_class=AgentStrategyProviderConfiguration,
        type_name="代理策略提供者",
        need_cwd_change=True,
        provider_name_attrs=["provider", "name"],
        count_attrs=["strategies"],
    ),
}


class PluginConfigProcessor:
    """
    插件配置类

    负责加载和管理插件的配置、工具、模型、代理策略等组件，
    提供插件运行时所需的类实例和配置信息。
    """

    # 插件基础配置
    configuration: PluginConfiguration

    # 工具提供者配置列表
    tools_configuration: list[ToolProviderConfiguration]

    # 代理策略提供者配置列表
    agent_strategies_configuration: list[AgentStrategyProviderConfiguration]

    # 模型提供者配置列表
    models_configuration: list[ModelProviderConfiguration]

    # 插件资源文件列表
    files: list[PluginAsset]

    def __init__(self, plugin_dir: Path) -> None:
        """
        初始化插件配置管理器

        Args:
            plugin_dir: 插件目录
        """
        # 初始化各种配置和映射
        self.tools_configuration = []
        self.models_configuration = []
        self.files = []
        self.agent_strategies_configuration = []
        self.plugin_dir = plugin_dir

    def _load_yaml_file_safely(self, file_path: Path) -> dict:
        """
        安全地加载YAML文件

        Args:
            file_path: YAML文件路径

        Returns:
            dict: 加载的YAML内容

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: YAML内容为空或解析失败
        """
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if not content:
                raise ValueError(f"配置文件为空: {file_path}")

            _logger.debug(f"成功加载YAML文件: {file_path}")
            return content

        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析失败: {file_path}, 错误: {e}")
        except Exception as e:
            raise ValueError(f"文件读取失败: {file_path}, 错误: {e}")

    def _extract_provider_info(
        self, configuration: Any, definition: ProviderConfigDefinition
    ) -> tuple[str, str]:
        """
        从配置对象中提取提供者信息

        Args:
            configuration: 配置对象
            definition: 配置定义

        Returns:
            tuple: (provider_name, extra_info)
        """
        # 提取提供者名称
        provider_name = "未知"
        if definition.provider_name_attrs:
            for attr in definition.provider_name_attrs:
                if hasattr(configuration, attr):
                    provider_name = getattr(configuration, attr, "未知")
                    break

        # 提取计数信息
        extra_info = ""
        if definition.count_attrs:
            for attr in definition.count_attrs:
                if hasattr(configuration, attr):
                    items = getattr(configuration, attr, [])
                    if items:
                        count = len(items)
                        attr_name = {
                            "models": "模型",
                            "tools": "工具",
                            "strategies": "策略",
                        }.get(attr, attr)
                        extra_info = f", {attr_name}数量: {count}"
                        break

        return provider_name, extra_info

    def _load_provider_configurations(
        self,
        provider_paths: list[str],
        definition: ProviderConfigDefinition,
        target_list: list[Any],
    ) -> None:
        """
        通用的提供者配置加载方法

        Args:
            provider_paths: 提供者配置文件路径列表
            definition: 配置定义
            target_list: 目标配置列表
        """
        for provider_path in provider_paths:
            try:
                full_path = self.plugin_dir / provider_path
                _logger.debug(f"正在加载{definition.type_name}配置文件: {full_path}")

                # 加载YAML内容
                config_data = self._load_yaml_file_safely(full_path)

                # 根据需要切换工作目录
                original_cwd = None
                if definition.need_cwd_change:
                    original_cwd = os.getcwd()
                    os.chdir(str(self.plugin_dir))

                try:
                    # 创建配置对象
                    configuration = definition.config_class(**config_data)
                    target_list.append(configuration)

                    # 提取并记录信息
                    provider_name, extra_info = self._extract_provider_info(
                        configuration, definition
                    )
                    _logger.info(
                        f"成功加载{definition.type_name}配置: {provider_name}{extra_info}"
                    )

                finally:
                    # 恢复工作目录
                    if original_cwd is not None:
                        os.chdir(original_cwd)

            except Exception as e:
                _logger.warning(
                    f"加载{definition.type_name}配置失败: {provider_path}, 原因: {e}"
                )
                continue

    def parse_plugin_config(self):
        # 加载插件配置文件
        self._load_plugin_configuration()
        # 加载插件资源文件
        self._load_plugin_assets()

    def _load_plugin_assets(self):
        """
        加载插件资源文件

        扫描 _assets 文件夹，将所有文件内容加载到内存中
        """
        # 检查并打开 _assets 文件夹
        with os.scandir(self.plugin_dir / "_assets") as entries:
            for entry in entries:
                if entry.is_file():
                    # 读取文件内容为字节数据
                    entry_bytes = Path(entry).read_bytes()
                    self.files.append(
                        PluginAsset(filename=entry.name, data=entry_bytes)
                    )

    def _load_plugin_configuration(self):
        """
        从 manifest.yaml 加载基础插件配置

        解析插件清单文件，加载工具、模型、端点、代理策略等配置
        """
        try:
            # 加载主配置文件
            file = load_yaml_file(str(self.plugin_dir / "manifest.yaml"))
            self.configuration = PluginConfiguration(**file)

            # 动态加载各种配置类型
            for config_key, definition in PROVIDER_CONFIG_DEFINITIONS.items():
                provider_paths = getattr(self.configuration.plugins, config_key, None)
                if provider_paths:
                    # 获取目标列表
                    target_list = getattr(self, f"{config_key}_configuration")
                    # 加载配置
                    self._load_provider_configurations(
                        provider_paths=provider_paths,
                        definition=definition,
                        target_list=target_list,
                    )

        except Exception as e:
            _logger.exception("加载插件配置时出错")
            raise ValueError(f"加载插件配置时出错: {e!s}") from e

    def get_plugin_config(self) -> PluginConfig:
        """
        获取插件配置

        Returns:
            PluginConfig: 插件配置
        """
        return PluginConfig(
            configuration=self.configuration,
            tools_configuration=self.tools_configuration,
            models_configuration=self.models_configuration,
            agent_strategies_configuration=self.agent_strategies_configuration,
        )
