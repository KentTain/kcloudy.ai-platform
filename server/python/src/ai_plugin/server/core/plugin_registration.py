import os
from pathlib import Path
from typing import TypeVar

from ai_plugin.sdk.entities.agent import (
    AgentStrategyConfiguration,
    AgentStrategyProviderConfiguration,
)
from ai_plugin.sdk.entities.endpoint import EndpointProviderConfiguration
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.provider import ModelProviderConfiguration
from ai_plugin.sdk.entities.tool import ToolConfiguration, ToolProviderConfiguration
from ai_plugin.sdk.interfaces.agent import AgentStrategy
from ai_plugin.sdk.interfaces.model import ModelProvider
from ai_plugin.sdk.interfaces.model.ai_model import AIModel
from ai_plugin.sdk.interfaces.model.large_language_model import LargeLanguageModel
from ai_plugin.sdk.interfaces.model.moderation_model import ModerationModel
from ai_plugin.sdk.interfaces.model.rerank_model import RerankModel
from ai_plugin.sdk.interfaces.model.speech2text_model import Speech2TextModel
from ai_plugin.sdk.interfaces.model.text_embedding_model import TextEmbeddingModel
from ai_plugin.sdk.interfaces.model.tts_model import TTSModel
from ai_plugin.sdk.interfaces.tool import Tool, ToolProvider
from ai_plugin.server.config.config import AlonPluginEnv
from ai_plugin.server.core.entities.plugin.setup import (
    PluginAsset,
    PluginConfiguration,
)
from ai_plugin.server.core.utils.class_loader import (
    load_multi_subclasses_from_source,
    load_single_subclass_from_source,
)
from ai_plugin.server.core.utils.yaml_loader import load_yaml_file
from ai_plugin.server.protocol.oauth import OAuthProviderProtocol

T = TypeVar("T")


class PluginRegistration:
    """
    插件注册管理类

    负责加载和管理插件的配置、工具、模型、代理策略等组件，
    提供插件运行时所需的类实例和配置信息。
    """

    # 插件基础配置
    configuration: PluginConfiguration

    # 工具提供者配置列表
    tools_configuration: list[ToolProviderConfiguration]

    # 工具映射：提供者名称 -> (配置, 提供者类, 工具映射)
    tools_mapping: dict[
        str,
        tuple[
            ToolProviderConfiguration,
            type[ToolProvider],
            dict[str, tuple[ToolConfiguration, type[Tool]]],
        ],
    ]

    # 代理策略提供者配置列表
    agent_strategies_configuration: list[AgentStrategyProviderConfiguration]

    # 代理策略映射：提供者名称 -> (配置, 策略映射)
    agent_strategies_mapping: dict[
        str,
        tuple[
            AgentStrategyProviderConfiguration,
            dict[str, tuple[AgentStrategyConfiguration, type[AgentStrategy]]],
        ],
    ]

    # 模型提供者配置列表
    models_configuration: list[ModelProviderConfiguration]

    # 模型映射：提供者名称 -> (配置, 提供者实例, 模型映射)
    models_mapping: dict[
        str,
        tuple[
            ModelProviderConfiguration,
            ModelProvider,
            dict[ModelType, AIModel],
        ],
    ]

    # 端点配置列表
    endpoints_configuration: list[EndpointProviderConfiguration]

    # 数据源配置（待实现）
    datasource_configuration: list[None]  # TBD

    # 数据源映射（待实现）
    datasource_mapping: dict[  # provider -> (provider_cls, datasource_mapping)
        str,
        tuple[
            None,
            dict[
                str, tuple[None, type[None]]
            ],  # datasource_name -> (datasource_configuration, datasource_cls)
        ],
    ]  # TBD

    # 插件资源文件列表
    files: list[PluginAsset]

    def __init__(self, config: AlonPluginEnv) -> None:
        """
        初始化插件注册管理器

        Args:
            config: 插件环境配置
        """
        # 初始化各种配置和映射
        self.tools_configuration = []
        self.models_configuration = []
        self.tools_mapping = {}
        self.models_mapping = {}
        self.endpoints_configuration = []
        self.files = []
        self.agent_strategies_configuration = []
        self.agent_strategies_mapping = {}

        # 加载插件配置文件
        self._load_plugin_configuration()
        # 解析插件类
        self._resolve_plugin_cls()
        # 加载插件资源文件
        self._load_plugin_assets()

    def _load_plugin_assets(self):
        """
        加载插件资源文件

        扫描 _assets 文件夹，将所有文件内容加载到内存中
        """
        # 检查并打开 _assets 文件夹
        with os.scandir("_assets") as entries:
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
            file = load_yaml_file("manifest.yaml")
            self.configuration = PluginConfiguration(**file)

            # 加载工具提供者配置
            for provider in self.configuration.plugins.tools:
                fs = load_yaml_file(provider)
                tool_provider_configuration = ToolProviderConfiguration(**fs)
                self.tools_configuration.append(tool_provider_configuration)

            # 加载模型提供者配置
            for provider in self.configuration.plugins.models:
                fs = load_yaml_file(provider)
                model_provider_configuration = ModelProviderConfiguration(**fs)
                self.models_configuration.append(model_provider_configuration)

            # 加载端点配置
            for provider in self.configuration.plugins.endpoints:
                fs = load_yaml_file(provider)
                endpoint_configuration = EndpointProviderConfiguration(**fs)
                self.endpoints_configuration.append(endpoint_configuration)

            # 加载代理策略配置
            for provider in self.configuration.plugins.agent_strategies:
                fs = load_yaml_file(provider)
                agent_provider_configuration = AgentStrategyProviderConfiguration(**fs)
                self.agent_strategies_configuration.append(agent_provider_configuration)

        except Exception as e:
            raise ValueError(f"加载插件配置时出错: {e!s}") from e

    def _resolve_tool_providers(self):
        """
        遍历所有工具提供者和工具，从源代码加载对应的类

        动态加载工具提供者类和工具类，建立运行时映射关系
        """
        for provider in self.tools_configuration:
            # 加载提供者类
            source = provider.extra.python.source
            # 移除文件扩展名
            module_source = os.path.splitext(source)[0]
            # 将路径分隔符替换为模块分隔符
            module_source = module_source.replace("/", ".")
            cls = load_single_subclass_from_source(
                module_name=module_source,
                script_path=os.path.join(os.getcwd(), source),
                parent_type=ToolProvider,
            )

            # 加载工具类
            tools = {}
            for tool in provider.tools:
                tool_source = tool.extra.python.source
                tool_module_source = os.path.splitext(tool_source)[0]
                tool_module_source = tool_module_source.replace("/", ".")
                tool_cls = load_single_subclass_from_source(
                    module_name=tool_module_source,
                    script_path=os.path.join(os.getcwd(), tool_source),
                    parent_type=Tool,
                )

                # 检查工具是否重写了运行时参数方法
                if tool_cls._is_get_runtime_parameters_overridden():
                    tool.has_runtime_parameters = True

                tools[tool.identity.name] = (tool, tool_cls)

            # 建立工具提供者映射
            self.tools_mapping[provider.identity.name] = (provider, cls, tools)

    def _resolve_agent_providers(self):
        """
        遍历所有代理提供者和策略，从源代码加载对应的类

        动态加载代理策略类，建立运行时映射关系
        """
        for provider in self.agent_strategies_configuration:
            strategies = {}
            for strategy in provider.strategies:
                strategy_source = strategy.extra.python.source
                strategy_module_source = os.path.splitext(strategy_source)[0]
                strategy_module_source = strategy_module_source.replace("/", ".")
                strategy_cls = load_single_subclass_from_source(
                    module_name=strategy_module_source,
                    script_path=os.path.join(os.getcwd(), strategy_source),
                    parent_type=AgentStrategy,
                )

                strategies[strategy.identity.name] = (strategy, strategy_cls)

            # 建立代理策略提供者映射
            self.agent_strategies_mapping[provider.identity.name] = (
                provider,
                strategies,
            )

    def _is_strict_subclass(self, cls: type[T], *parent_cls: type[T]) -> bool:
        """
        检查类是否为指定父类的严格子类

        Args:
            cls: 要检查的类
            parent_cls: 父类列表

        Returns:
            bool: 如果是严格子类则返回 True
        """
        return any(issubclass(cls, parent) and cls != parent for parent in parent_cls)

    def _resolve_model_providers(self):
        """
        遍历所有模型提供者和模型，从源代码加载对应的类

        动态加载模型提供者类和各种模型类，建立运行时映射关系
        """
        for provider in self.models_configuration:
            # 加载模型提供者类
            source = provider.extra.python.provider_source
            # 移除文件扩展名
            module_source = os.path.splitext(source)[0]
            # 将路径分隔符替换为模块分隔符
            module_source = module_source.replace("/", ".")
            cls = load_single_subclass_from_source(
                module_name=module_source,
                script_path=os.path.join(os.getcwd(), source),
                parent_type=ModelProvider,
            )

            # 加载模型类
            models = {}
            for model_source in provider.extra.python.model_sources:
                model_module_source = os.path.splitext(model_source)[0]
                model_module_source = model_module_source.replace("/", ".")
                model_classes = load_multi_subclasses_from_source(
                    module_name=model_module_source,
                    script_path=os.path.join(os.getcwd(), model_source),
                    parent_type=AIModel,
                )

                # 为每个模型类创建实例并按类型分类
                for model_cls in model_classes:
                    if self._is_strict_subclass(
                        model_cls,
                        LargeLanguageModel,
                        TextEmbeddingModel,
                        RerankModel,
                        TTSModel,
                        Speech2TextModel,
                        ModerationModel,
                    ):
                        models[model_cls.model_type] = model_cls(provider.models)  # type: ignore

            # 创建提供者实例并建立映射
            provider_instance = cls(provider, models)  # type: ignore
            self.models_mapping[provider.provider] = (
                provider,
                provider_instance,
                models,
            )

    def _resolve_plugin_cls(self):
        """
        解析插件类

        加载工具提供者、模型提供者、代理策略等所有插件组件的类
        """
        # 加载工具提供者和工具
        self._resolve_tool_providers()

        # 加载模型提供者和模型
        self._resolve_model_providers()

        # 加载代理提供者和策略
        self._resolve_agent_providers()

    def get_tool_provider_cls(self, provider: str):
        """
        根据提供者名称获取工具提供者类

        Args:
            provider: 提供者名称

        Returns:
            工具提供者类，如果不存在则返回 None
        """
        for provider_registration in self.tools_mapping:
            if provider_registration == provider:
                return self.tools_mapping[provider_registration][1]

    def get_tool_cls(self, provider: str, tool: str):
        """
        根据提供者和工具名称获取工具类

        Args:
            provider: 提供者名称
            tool: 工具名称

        Returns:
            工具类，如果不存在则返回 None
        """
        for provider_registration in self.tools_mapping:
            if provider_registration == provider:
                registration = self.tools_mapping[provider_registration][2].get(tool)
                if registration:
                    return registration[1]

    def get_agent_provider_cls(self, provider: str):
        """
        根据提供者名称获取代理提供者类

        Args:
            provider: 提供者名称

        Returns:
            代理提供者类，如果不存在则返回 None
        """
        for provider_registration in self.agent_strategies_mapping:
            if provider_registration == provider:
                return self.agent_strategies_mapping[provider_registration][1]

    def get_agent_strategy_cls(self, provider: str, agent: str):
        """
        根据提供者和代理名称获取代理策略类

        Args:
            provider: 提供者名称
            agent: 代理策略名称

        Returns:
            代理策略类，如果不存在则返回 None
        """
        for provider_registration in self.agent_strategies_mapping:
            if provider_registration == provider:
                registration = self.agent_strategies_mapping[provider_registration][
                    1
                ].get(agent)
                if registration:
                    return registration[1]

    def get_model_provider_instance(self, provider: str):
        """
        根据提供者名称获取模型提供者实例

        Args:
            provider: 提供者名称

        Returns:
            模型提供者实例，如果不存在则返回 None
        """
        for provider_registration in self.models_mapping:
            if provider_registration == provider:
                return self.models_mapping[provider_registration][1]

    def get_model_instance(self, provider: str, model_type: ModelType):
        """
        根据提供者和模型类型获取模型实例

        Args:
            provider: 提供者名称
            model_type: 模型类型

        Returns:
            模型实例，如果不存在则返回 None
        """
        for provider_registration in self.models_mapping:
            if provider_registration == provider:
                registration = self.models_mapping[provider_registration][2].get(
                    model_type
                )
                if registration:
                    return registration

    def get_supported_oauth_provider_cls(
        self, provider: str
    ) -> type[OAuthProviderProtocol] | None:
        """
        获取支持 OAuth 的提供者类

        Args:
            provider: 提供者名称

        Returns:
            支持 OAuth 的提供者类，如果不存在则返回 None
        """
        for provider_registration in self.tools_mapping:
            if (
                provider_registration == provider
                and self.tools_mapping[provider_registration][0].oauth_schema
            ):
                return self.tools_mapping[provider_registration][1]

        return None
