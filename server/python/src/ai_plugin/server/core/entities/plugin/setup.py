import datetime
from enum import Enum

from pydantic import BaseModel, Field

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.server.core.documentation.schema_doc import docs


@docs(
    description="插件架构类型",
)
class PluginArch(Enum):
    """插件架构枚举"""

    AMD64 = "amd64"  # AMD64架构
    ARM64 = "arm64"  # ARM64架构


@docs(
    description="插件编程语言",
)
class PluginLanguage(Enum):
    """插件编程语言枚举"""

    PYTHON = "python"  # Python语言


@docs(
    description="插件类型",
)
class PluginType(Enum):
    """插件类型枚举"""

    Plugin = "plugin"  # 插件类型


@docs(
    description="插件资源需求",
)
class PluginResourceRequirements(BaseModel):
    """插件资源需求类"""

    memory: int  # 内存需求（字节）

    @docs(
        description="插件权限配置",
    )
    class Permission(BaseModel):
        """插件权限配置类"""

        @docs(
            description="工具权限配置",
        )
        class Tool(BaseModel):
            """工具权限配置类"""

            enabled: bool | None = Field(default=False, description="是否启用工具调用")

        @docs(
            description="模型权限配置",
        )
        class Model(BaseModel):
            """模型权限配置类"""

            enabled: bool | None = Field(default=False, description="是否启用模型调用")
            llm: bool | None = Field(
                default=False, description="是否启用大语言模型调用"
            )
            text_embedding: bool | None = Field(
                default=False, description="是否启用文本嵌入调用"
            )
            rerank: bool | None = Field(default=False, description="是否启用重排序调用")
            tts: bool | None = Field(
                default=False, description="是否启用文本转语音调用"
            )
            speech2text: bool | None = Field(
                default=False, description="是否启用语音转文本调用"
            )
            moderation: bool | None = Field(
                default=False, description="是否启用内容审核调用"
            )

        @docs(
            description="节点权限配置",
        )
        class Node(BaseModel):
            """节点权限配置类"""

            enabled: bool | None = Field(default=False, description="是否启用节点调用")

        @docs(
            description="端点权限配置",
        )
        class Endpoint(BaseModel):
            """端点权限配置类"""

            enabled: bool | None = Field(default=False, description="是否启用端点注册")

        @docs(
            description="应用权限配置",
        )
        class App(BaseModel):
            """应用权限配置类"""

            enabled: bool | None = Field(default=False, description="是否启用应用调用")

        @docs(
            description="存储权限配置",
        )
        class Storage(BaseModel):
            """存储权限配置类"""

            enabled: bool | None = Field(default=False, description="是否启用存储使用")
            size: int = Field(
                ge=1024,
                le=1073741824,
                default=1048576,
                description="存储大小限制（字节）",
            )

        tool: Tool | None = Field(default=None, description="工具权限配置")
        model: Model | None = Field(default=None, description="模型权限配置")
        node: Node | None = Field(default=None, description="节点权限配置")
        endpoint: Endpoint | None = Field(default=None, description="端点权限配置")
        app: App | None = Field(default=None, description="应用权限配置")
        storage: Storage | None = Field(default=None, description="存储权限配置")

    permission: Permission | None = Field(default=None, description="插件权限配置")


@docs(
    name="Manifest",
    description="插件清单文档",
    top=True,
)
class PluginConfiguration(BaseModel):
    """插件配置类，定义插件的完整配置信息"""

    @docs(
        description="插件扩展配置",
    )
    class Plugins(BaseModel):
        """插件扩展配置类"""

        tools: list[str] = Field(
            default_factory=list,
            description="工具提供者的清单路径列表（yaml格式），参考 [ToolProvider](#toolprovider)",
        )
        models: list[str] = Field(
            default_factory=list,
            description="模型提供者的清单路径列表（yaml格式），参考 [ModelProvider](#modelprovider)",
        )
        endpoints: list[str] = Field(
            default_factory=list,
            description="端点组的清单路径列表（yaml格式），参考 [EndpointGroup](#endpointgroup)",
        )
        agent_strategies: list[str] = Field(
            default_factory=list,
            description="代理策略提供者的清单路径列表（yaml格式），"
            "参考 [AgentStrategyProvider](#agentstrategyprovider)",
        )

    @docs(
        description="插件元信息",
    )
    class Meta(BaseModel):
        """插件元信息类"""

        @docs(
            description="插件运行器配置",
        )
        class PluginRunner(BaseModel):
            """插件运行器配置类"""

            language: PluginLanguage  # 编程语言
            version: str  # 语言版本
            entrypoint: str  # 入口点

        version: str  # 元信息版本
        arch: list[PluginArch]  # 支持的架构列表
        runner: PluginRunner  # 运行器配置
        minimum_dify_version: str | None = Field(
            None,
            pattern=r"^\d{1,4}(\.\d{1,4}){1,3}(-\w{1,16})?$",
            description="最低支持的Dify版本",
        )

    version: str = Field(
        ..., pattern=r"^\d{1,4}(\.\d{1,4}){1,3}(-\w{1,16})?$", description="插件版本"
    )
    type: PluginType  # 插件类型
    author: str | None = Field(
        ..., pattern=r"^[a-zA-Z0-9_-]{1,64}$", description="插件作者"
    )
    name: str = Field(..., pattern=r"^[a-z0-9_-]{1,128}$", description="插件名称")
    repo: str | None = Field(None, description="插件仓库URL")
    description: I18nObject  # 插件描述（多语言）
    icon: str  # 插件图标
    label: I18nObject  # 插件标签（多语言）
    created_at: datetime.datetime  # 创建时间
    resource: PluginResourceRequirements  # 资源需求
    plugins: Plugins  # 扩展配置
    meta: Meta  # 元信息


@docs(
    description="插件提供者类型",
)
class PluginProviderType(Enum):
    """插件提供者类型枚举"""

    Tool = "tool"  # 工具提供者
    Model = "model"  # 模型提供者
    Endpoint = "endpoint"  # 端点提供者


class PluginAsset(BaseModel):
    """插件资源类"""

    filename: str  # 文件名
    data: bytes  # 文件数据
