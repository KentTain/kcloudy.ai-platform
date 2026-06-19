import base64
import contextlib
import json
import uuid
from collections.abc import Mapping
from enum import Enum, StrEnum
from typing import Any

from docstring_parser import DocstringParam
from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model.message import PromptMessageTool
from ai_plugin.sdk.entities.oauth import OAuthSchema
from ai_plugin.sdk.entities.provider_config import (
    CommonParameterType,
    LogMetadata,
    ProviderConfig,
)
from ai_plugin.server.core.documentation.schema_doc import docs
from ai_plugin.server.core.utils.yaml_loader import load_yaml_file


class ToolRuntime(BaseModel):
    """
    工具运行时配置模型类

    存储工具执行时的运行时信息，包括凭证、用户ID和会话ID
    """

    credentials: dict[str, Any]  # 凭证信息字典
    user_id: str | None  # 用户ID（可选）
    session_id: str | None  # 会话ID（可选）


class ToolInvokeMessage(BaseModel):
    """
    工具调用消息模型类

    定义工具调用过程中产生的各种类型消息，支持文本、JSON、二进制数据等多种消息格式
    """

    class TextMessage(BaseModel):
        """
        文本消息子类

        用于传递纯文本内容
        """

        text: str  # 文本内容

        def to_dict(self):
            """
            转换为字典格式

            Returns:
                dict: 包含文本内容的字典
            """
            return {"text": self.text}

    class JsonMessage(BaseModel):
        """
        JSON消息子类

        用于传递结构化的JSON数据
        """

        json_object: Mapping | list  # JSON对象或列表

        def to_dict(self):
            """
            转换为字典格式

            Returns:
                dict: 包含JSON对象的字典
            """
            return {"json_object": self.json_object}

    class BlobMessage(BaseModel):
        """
        二进制数据消息子类

        用于传递二进制数据，如文件内容
        """

        blob: bytes  # 二进制数据

    class BlobChunkMessage(BaseModel):
        """
        二进制数据块消息子类

        用于分块传输大型二进制数据
        """

        id: str = Field(..., description="数据块的ID")
        sequence: int = Field(..., description="数据块的序号")
        total_length: int = Field(..., description="二进制数据的总长度")
        blob: bytes = Field(..., description="数据块的二进制内容")
        end: bool = Field(..., description="是否为最后一个数据块")

    class VariableMessage(BaseModel):
        """
        变量消息子类

        用于传递变量值，支持流式传输
        """

        variable_name: str = Field(
            ...,
            description="变量名称，仅支持根级变量",
        )
        variable_value: Any = Field(..., description="变量的值")
        stream: bool = Field(default=False, description="是否以流式方式传输变量")

        @model_validator(mode="before")
        @classmethod
        def validate_variable_value_and_stream(cls, values):
            """
            验证变量值和流式传输的一致性

            当启用流式传输时，变量值必须是字符串类型

            Args:
                values: 验证的值

            Returns:
                验证后的值

            Raises:
                ValueError: 当流式传输启用但变量值不是字符串时抛出
            """
            # 如果值不是字典则跳过验证
            if not isinstance(values, dict):
                return values

            if values.get("stream") and not isinstance(
                values.get("variable_value"), str
            ):
                raise ValueError("当'stream'为True时，'variable_value'必须是字符串。")
            return values

    class LogMessage(BaseModel):
        """
        日志消息子类

        用于记录工具执行过程中的日志信息
        """

        class LogStatus(Enum):
            """
            日志状态枚举

            定义日志的不同状态
            """

            START = "start"  # 开始状态
            ERROR = "error"  # 错误状态
            SUCCESS = "success"  # 成功状态

        id: str = Field(
            default_factory=lambda: str(uuid.uuid4()), description="日志的ID"
        )
        label: str = Field(..., description="日志的标签")
        parent_id: str | None = Field(
            default=None, description="父级日志ID，根日志留空"
        )
        error: str | None = Field(default=None, description="错误信息")
        status: LogStatus = Field(..., description="日志状态")
        data: Mapping[str, Any] = Field(..., description="详细的日志数据")
        metadata: Mapping[LogMetadata, Any] | None = Field(
            default=None, description="日志的元数据"
        )

    class RetrieverResourceMessage(BaseModel):
        """
        检索资源消息子类

        用于传递检索到的资源信息和上下文
        """

        class RetrieverResource(BaseModel):
            """
            检索资源模型类

            定义单个检索资源的详细信息
            """

            position: int | None = None  # 位置
            dataset_id: str | None = None  # 数据集ID
            dataset_name: str | None = None  # 数据集名称
            document_id: str | None = None  # 文档ID
            document_name: str | None = None  # 文档名称
            data_source_type: str | None = None  # 数据源类型
            segment_id: str | None = None  # 段落ID
            retriever_from: str | None = None  # 检索来源
            score: float | None = None  # 相关性分数
            hit_count: int | None = None  # 命中次数
            word_count: int | None = None  # 字数
            segment_position: int | None = None  # 段落位置
            index_node_hash: str | None = None  # 索引节点哈希
            content: str | None = None  # 内容
            page: int | None = None  # 页码
            doc_metadata: dict | None = None  # 文档元数据

        retriever_resources: list[RetrieverResource] = Field(
            ..., description="检索到的资源列表"
        )
        context: str = Field(..., description="上下文信息")

    class MessageType(Enum):
        """
        消息类型枚举

        定义工具调用消息支持的各种类型
        """

        TEXT = "text"  # 文本消息
        FILE = "file"  # 文件消息
        BLOB = "blob"  # 二进制数据消息
        JSON = "json"  # JSON消息
        LINK = "link"  # 链接消息
        IMAGE = "image"  # 图片消息
        IMAGE_LINK = "image_link"  # 图片链接消息
        BINARY_LINK = "binary_link"  # 二进制链接消息
        VARIABLE = "variable"  # 变量消息
        BLOB_CHUNK = "blob_chunk"  # 二进制数据块消息
        LOG = "log"  # 日志消息
        RETRIEVER_RESOURCES = "retriever_resources"  # 检索资源消息

    type: MessageType  # 消息类型
    # TODO: pydantic将逐一验证和构造消息，直到遇到正确的类型
    # 我们需要优化构造过程
    message: (
        TextMessage
        | JsonMessage
        | VariableMessage
        | BlobMessage
        | BlobChunkMessage
        | LogMessage
        | RetrieverResourceMessage
        | None
    )  # 消息内容
    meta: dict | None = None  # 元数据（可选）

    @field_validator("message", mode="before")
    @classmethod
    def decode_blob_message(cls, v):
        """
        解码二进制消息

        将base64编码的二进制数据解码为bytes

        Args:
            v: 消息值

        Returns:
            解码后的消息值
        """
        if isinstance(v, dict) and "blob" in v:
            with contextlib.suppress(Exception):
                v["blob"] = base64.b64decode(v["blob"])
        return v

    @field_serializer("message")
    def serialize_message(self, v):
        """
        序列化消息

        将二进制数据编码为base64格式以便传输

        Args:
            v: 消息对象

        Returns:
            序列化后的消息
        """
        if isinstance(v, self.BlobMessage):
            return {"blob": base64.b64encode(v.blob).decode("utf-8")}
        elif isinstance(v, self.BlobChunkMessage):
            return {
                "id": v.id,
                "sequence": v.sequence,
                "total_length": v.total_length,
                "blob": base64.b64encode(v.blob).decode("utf-8"),
                "end": v.end,
            }
        return v


@docs(
    description="工具标识",
)
class ToolIdentity(BaseModel):
    """
    工具标识模型类

    定义工具的基本身份信息，包括作者、名称和标签
    """

    author: str = Field(..., description="工具的作者")
    name: str = Field(..., description="工具的名称")
    label: I18nObject = Field(..., description="工具的标签")


@docs(
    description="工具参数选项",
)
class ToolParameterOption(BaseModel):
    """
    工具参数选项模型类

    定义选择器类型参数的可选项
    """

    value: str = Field(..., description="选项的值")
    label: I18nObject = Field(..., description="选项的标签")

    @field_validator("value", mode="before")
    @classmethod
    def transform_id_to_str(cls, value) -> str:
        """
        将ID转换为字符串

        确保选项值始终为字符串类型

        Args:
            value: 选项值

        Returns:
            str: 字符串格式的选项值
        """
        if not isinstance(value, str):
            return str(value)
        else:
            return value


@docs(
    description="参数自动生成配置",
)
class ParameterAutoGenerate(BaseModel):
    """
    参数自动生成配置模型类

    定义参数的自动生成方式
    """

    class Type(StrEnum):
        """
        自动生成类型枚举

        定义支持的自动生成类型
        """

        PROMPT_INSTRUCTION = "prompt_instruction"  # 提示指令

    type: Type  # 自动生成类型


@docs(
    description="参数模板配置",
)
class ParameterTemplate(BaseModel):
    """
    参数模板配置模型类

    定义参数模板的配置信息
    """

    enabled: bool = Field(..., description="是否启用Jinja模板")


@docs(
    description="参数类型",
)
class ToolParameter(BaseModel):
    """
    工具参数模型类

    定义工具参数的完整配置信息，包括类型、验证规则、显示信息等
    """

    class ToolParameterType(str, Enum):
        """
        工具参数类型枚举

        定义工具参数支持的各种数据类型
        """

        STRING = CommonParameterType.STRING.value  # 字符串类型
        NUMBER = CommonParameterType.NUMBER.value  # 数字类型
        BOOLEAN = CommonParameterType.BOOLEAN.value  # 布尔类型
        SELECT = CommonParameterType.SELECT.value  # 选择器类型
        SECRET_INPUT = CommonParameterType.SECRET_INPUT.value  # 密钥输入类型
        FILE = CommonParameterType.FILE.value  # 文件类型
        FILES = CommonParameterType.FILES.value  # 多文件类型
        MODEL_SELECTOR = CommonParameterType.MODEL_SELECTOR.value  # 模型选择器类型
        APP_SELECTOR = CommonParameterType.APP_SELECTOR.value  # 应用选择器类型
        # TOOL_SELECTOR = CommonParameterType.TOOL_SELECTOR.value  # 工具选择器类型（已废弃）
        ANY = CommonParameterType.ANY.value  # 任意类型

    class ToolParameterForm(Enum):
        """
        工具参数表单类型枚举

        定义参数在不同阶段的表单类型
        """

        SCHEMA = "schema"  # 架构阶段，添加工具时设置
        FORM = "form"  # 表单阶段，调用工具前设置
        LLM = "llm"  # LLM阶段，由大语言模型设置

    name: str = Field(..., description="参数的名称")
    label: I18nObject = Field(..., description="呈现给用户的标签")
    human_description: I18nObject = Field(..., description="呈现给用户的描述")
    type: ToolParameterType = Field(..., description="参数的类型")
    auto_generate: ParameterAutoGenerate | None = Field(
        default=None, description="参数的自动生成配置"
    )
    template: ParameterTemplate | None = Field(
        default=None, description="参数的模板配置"
    )
    scope: str | None = None  # 作用域（可选）
    form: ToolParameterForm = Field(..., description="参数的表单类型，schema/form/llm")
    llm_description: str | None = None  # LLM描述（可选）
    required: bool | None = False  # 是否必填
    default: int | float | str | None = None  # 默认值
    min: float | int | None = None  # 最小值
    max: float | int | None = None  # 最大值
    precision: int | None = None  # 精度
    options: list[ToolParameterOption] | None = None  # 选项列表

    def to_docstring_param(self) -> DocstringParam:
        """
        将工具参数转换为Google风格的Docstring
        """

        prompt = ""
        description = (
            self.llm_description
            if self.llm_description
            else self.human_description.path
        )

        prompt += f"{description}\n"

        rule = {}

        if self.min:
            rule["min"] = self.min

        if self.max:
            rule["max"] = self.max

        if self.precision:
            rule["precision"] = self.precision

        if len(rule) > 0:
            prompt += f"  Parameter rule: {json.dumps(rule, ensure_ascii=False)}\n"

        if self.options and len(self.options) > 0:
            options = [
                {"label": option.label.path, "value": option.value}
                for option in self.options
            ]
            prompt += (
                f"  Available options: {json.dumps(options, ensure_ascii=False)}\n"
            )

        return DocstringParam(
            args=["param", self.name],
            description=prompt,
            arg_name=self.name,
            type_name=self.type.value,
            is_optional=not self.required,
            default=str(self.default) if self.default else None,
        )


@docs(
    description="工具描述",
)
class ToolDescription(BaseModel):
    """
    工具描述模型类

    定义工具的描述信息，分别面向用户和LLM
    """

    human: I18nObject = Field(..., description="呈现给用户的描述")
    llm: str = Field(..., description="呈现给LLM的描述")


@docs(
    name="ToolExtra",
    description="工具额外配置",
)
class ToolConfigurationExtra(BaseModel):
    """
    工具配置额外信息模型类

    存储工具的额外配置信息，如Python源码等
    """

    class Python(BaseModel):
        """
        Python配置子类

        存储Python相关的配置信息
        """

        source: str  # Python源码路径或内容

    python: Python  # Python配置


@docs(
    name="Tool",
    description="工具配置清单",
)
class ToolConfiguration(BaseModel):
    """
    工具配置模型类

    定义单个工具的完整配置信息
    """

    identity: ToolIdentity  # 工具标识
    parameters: list[ToolParameter] = Field(default=[], description="工具的参数列表")
    description: ToolDescription  # 工具描述
    extra: ToolConfigurationExtra  # 额外配置
    has_runtime_parameters: bool = Field(default=False, description="是否有运行时参数")
    output_schema: Mapping[str, Any] | None = None  # 输出架构（可选）


@docs(
    description="工具标签",
)
class ToolLabelEnum(Enum):
    """
    工具标签枚举类

    定义工具的分类标签，用于工具的分类和检索
    """

    SEARCH = "search"  # 搜索类
    IMAGE = "image"  # 图像类
    VIDEOS = "videos"  # 视频类
    WEATHER = "weather"  # 天气类
    FINANCE = "finance"  # 金融类
    DESIGN = "design"  # 设计类
    TRAVEL = "travel"  # 旅行类
    SOCIAL = "social"  # 社交类
    NEWS = "news"  # 新闻类
    MEDICAL = "medical"  # 医疗类
    PRODUCTIVITY = "productivity"  # 生产力类
    EDUCATION = "education"  # 教育类
    BUSINESS = "business"  # 商业类
    ENTERTAINMENT = "entertainment"  # 娱乐类
    UTILITIES = "utilities"  # 实用工具类
    OTHER = "other"  # 其他类


@docs(
    description="工具提供者标识",
)
class ToolProviderIdentity(BaseModel):
    """
    工具提供者标识模型类

    定义工具提供者的基本身份信息
    """

    author: str = Field(..., description="工具的作者")
    name: str = Field(..., description="工具的名称")
    description: I18nObject = Field(..., description="工具的描述")
    icon: str = Field(..., description="工具的图标")
    label: I18nObject = Field(..., description="工具的标签")
    tags: list[ToolLabelEnum] = Field(
        default=[],
        description="工具的标签列表",
    )


@docs(
    name="ToolProviderExtra",
    description="工具提供者额外配置",
)
class ToolProviderConfigurationExtra(BaseModel):
    """
    工具提供者配置额外信息模型类

    存储工具提供者的额外配置信息
    """

    class Python(BaseModel):
        """
        Python配置子类

        存储Python相关的配置信息
        """

        source: str  # Python源码路径或内容

    python: Python  # Python配置


@docs(
    name="ToolProvider",
    description="工具提供者配置清单",
    outside_reference_fields={"tools": ToolConfiguration},
)
class ToolProviderConfiguration(BaseModel):
    """
    工具提供者配置模型类

    定义工具提供者的完整配置，包括身份信息、凭证架构、OAuth配置和工具列表
    """

    identity: ToolProviderIdentity  # 提供者标识
    credentials_schema: list[ProviderConfig] = Field(
        default_factory=list,
        alias="credentials_for_provider",
        description="工具提供者的凭证架构",
    )
    oauth_schema: OAuthSchema | None = Field(
        default=None,
        description="如果支持OAuth则提供OAuth架构",
    )
    tools: list[ToolConfiguration] = Field(default=[], description="提供者的工具列表")
    extra: ToolProviderConfigurationExtra  # 额外配置

    @model_validator(mode="before")
    @classmethod
    def validate_credentials_schema(cls, data: dict) -> dict:
        """
        验证凭证架构

        将原始凭证配置转换为标准格式

        Args:
            data: 原始数据

        Returns:
            dict: 验证后的数据
        """
        original_credentials_for_provider: dict[str, dict] = data.get(
            "credentials_for_provider", {}
        )

        credentials_for_provider: list[dict[str, Any]] = []
        for name, credential in original_credentials_for_provider.items():
            credential["name"] = name
            credentials_for_provider.append(credential)

        data["credentials_for_provider"] = credentials_for_provider
        return data

    @field_validator("tools", mode="before")
    @classmethod
    def validate_tools(cls, value) -> list[ToolConfiguration]:
        """
        验证工具配置列表

        从YAML文件加载工具配置

        Args:
            value: 工具配置值

        Returns:
            list[ToolConfiguration]: 验证后的工具配置列表

        Raises:
            ValueError: 当配置格式无效时抛出
        """
        if not isinstance(value, list):
            raise ValueError("工具配置应该是一个列表")

        tools: list[ToolConfiguration] = []

        for tool in value:
            # 从YAML文件读取
            if isinstance(tool, dict):
                # 兼容从数据库反序列化回来的数据
                tools.append(ToolConfiguration(**tool))
                continue

            if not isinstance(tool, str):
                raise ValueError("工具路径应该是字符串")
            try:
                file = load_yaml_file(tool)
                tools.append(
                    ToolConfiguration(
                        identity=ToolIdentity(**file["identity"]),
                        parameters=[
                            ToolParameter(**param)
                            for param in file.get("parameters", []) or []
                        ],
                        description=ToolDescription(**file["description"]),
                        extra=ToolConfigurationExtra(**file.get("extra", {})),
                        output_schema=file.get("output_schema", None),
                    ),
                )
            except Exception as e:
                raise ValueError(f"加载工具配置时出错: {e!s}") from e

        return tools


class ToolProviderType(Enum):
    """
    工具提供者类型枚举类

    定义不同类型的工具提供者
    """

    BUILT_IN = "builtin"  # 内置工具
    WORKFLOW = "workflow"  # 工作流工具
    API = "api"  # API工具
    APP = "app"  # 应用工具
    DATASET_RETRIEVAL = "dataset-retrieval"  # 数据集检索工具
    MCP = "mcp"  # MCP工具
    PLUGIN = "plugin"  # 插件工具

    @classmethod
    def value_of(cls, value: str) -> "ToolProviderType":
        """
        根据给定值获取对应的提供者类型

        Args:
            value: 提供者类型值

        Returns:
            ToolProviderType: 提供者类型枚举

        Raises:
            ValueError: 当提供者类型值无效时抛出
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"无效的提供者类型值 {value}")


class ToolSelector(BaseModel):
    """
    工具选择器模型类

    用于选择和配置特定的工具，包含工具的基本信息和参数配置
    """

    class Parameter(BaseModel):
        """
        参数子类

        定义工具选择器中的参数信息
        """

        name: str = Field(..., description="参数的名称")
        type: ToolParameter.ToolParameterType = Field(..., description="参数的类型")
        required: bool = Field(..., description="参数是否必填")
        description: str = Field(..., description="参数的描述")
        default: int | float | str | None = None  # 默认值
        options: list[ToolParameterOption] | None = None  # 选项列表

    provider_id: str = Field(..., description="提供者的ID")
    tool_name: str = Field(..., description="工具的名称")
    tool_description: str = Field(..., description="工具的描述")
    tool_configuration: Mapping[str, Any] = Field(..., description="配置信息，表单类型")
    tool_parameters: Mapping[str, Parameter] = Field(
        ..., description="参数信息，LLM类型"
    )

    def to_prompt_message(self) -> PromptMessageTool:
        """
        将工具选择器转换为提示消息工具，基于OpenAI函数调用架构

        Returns:
            PromptMessageTool: 转换后的提示消息工具
        """
        tool = PromptMessageTool(
            name=self.tool_name,
            description=self.tool_description,
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

        for name, parameter in self.tool_parameters.items():
            param_dict = {
                "type": parameter.type.value,
                "description": parameter.description,
            }

            if parameter.required:
                tool.parameters["required"].append(name)

            if parameter.options:
                param_dict["enum"] = [option.value for option in parameter.options]

            tool.parameters["properties"][name] = param_dict

        return tool

    def to_plugin_parameter(self) -> dict[str, Any]:
        return self.model_dump()
