import glob
import os
from collections.abc import Sequence
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model import AIModelEntity, ModelType
from ai_plugin.server.core.documentation.schema_doc import docs
from ai_plugin.server.core.utils.yaml_loader import load_yaml_file


@docs(
    description="配置方法",
    name="ModelConfigurateMethod",
)
class ConfigurateMethod(Enum):
    """
    提供者模型配置方法枚举类

    定义模型的配置方式
    """

    PREDEFINED_MODEL = "predefined-model"  # 预定义模型
    CUSTOMIZABLE_MODEL = "customizable-model"  # 可自定义模型


@docs(
    description="模型表单类型",
    name="ModelFormType",
)
class FormType(Enum):
    """
    表单类型枚举类

    定义配置表单的各种控件类型
    """

    TEXT_INPUT = "text-input"  # 文本输入
    SECRET_INPUT = "secret-input"  # 密码输入
    SELECT = "select"  # 下拉选择
    RADIO = "radio"  # 单选按钮
    SWITCH = "switch"  # 开关


@docs(
    description="表单显示条件",
    name="ModelFormShowOnObject",
)
class FormShowOnObject(BaseModel):
    """
    表单显示条件模型类

    定义表单项的显示条件
    """

    variable: str  # 变量名
    value: str  # 变量值


@docs(
    description="表单选项",
    name="ModelFormOption",
)
class FormOption(BaseModel):
    """
    表单选项模型类

    定义下拉框或单选按钮的选项
    """

    label: I18nObject  # 选项标签
    value: str  # 选项值
    show_on: list[FormShowOnObject] = Field(default_factory=list)  # 显示条件

    def __init__(self, **data):
        """
        初始化表单选项

        如果未提供标签，则使用值作为默认标签
        """
        super().__init__(**data)
        if not self.label:
            self.label = I18nObject(en_US=self.value)


@docs(
    description="凭证表单架构",
    name="ModelCredentialFormSchema",
)
class CredentialFormSchema(BaseModel):
    """
    凭证表单架构模型类

    定义配置表单中单个字段的架构
    """

    variable: str  # 变量名
    label: I18nObject  # 字段标签
    type: FormType  # 字段类型
    required: bool = True  # 是否必填
    default: str | None = None  # 默认值
    options: list[FormOption] | None = None  # 选项列表（用于下拉框和单选按钮）
    placeholder: I18nObject | None = None  # 占位符文本
    max_length: int = 0  # 最大长度
    show_on: list[FormShowOnObject] = Field(default_factory=list)  # 显示条件


@docs(
    description="模型提供者凭证架构",
    name="ModelProviderCredentialSchema",
)
class ProviderCredentialSchema(BaseModel):
    """
    提供者凭证架构模型类

    定义提供者级别的凭证配置架构
    """

    credential_form_schemas: list[CredentialFormSchema]  # 凭证表单架构列表


@docs(
    description="字段模型架构",
    name="ModelFieldModelSchema",
)
class FieldModelSchema(BaseModel):
    """
    字段模型架构类

    定义模型字段的显示架构
    """

    label: I18nObject  # 字段标签
    placeholder: I18nObject | None = None  # 占位符文本


class ModelCredentialSchema(BaseModel):
    """
    模型凭证架构模型类

    定义模型级别的凭证配置架构
    """

    model: FieldModelSchema  # 模型字段架构
    credential_form_schemas: list[CredentialFormSchema]  # 凭证表单架构列表


class SimpleProviderEntity(BaseModel):
    """
    简单提供者实体模型类

    提供者的简化信息，用于列表显示
    """

    provider: str  # 提供者名称
    label: I18nObject  # 提供者标签
    icon_small: I18nObject | None = None  # 小图标
    icon_large: I18nObject | None = None  # 大图标
    supported_model_types: Sequence[ModelType]  # 支持的模型类型列表
    models: list[AIModelEntity] = []  # 模型列表


@docs(
    description="模型提供者帮助",
    name="ModelProviderHelp",
)
class ProviderHelpEntity(BaseModel):
    """
    提供者帮助实体模型类

    定义提供者的帮助信息
    """

    title: I18nObject  # 帮助标题
    url: I18nObject  # 帮助链接


@docs(
    description="模型位置",
    name="ModelPosition",
)
class ModelPosition(BaseModel):
    """
    AI模型位置模型类

    定义各类型模型的排序位置
    """

    llm: list[str] | None = Field(
        default_factory=list, description="LLM模型按升序排列，在此填写模型名称"
    )
    text_embedding: list[str] | None = Field(
        default_factory=list,
        description="文本嵌入模型按升序排列，在此填写模型名称",
    )
    rerank: list[str] | None = Field(
        default_factory=list, description="重排序模型按升序排列，在此填写模型名称"
    )
    tts: list[str] | None = Field(
        default_factory=list, description="TTS模型按升序排列，在此填写模型名称"
    )
    speech2text: list[str] | None = Field(
        default_factory=list,
        description="语音转文本模型按升序排列，在此填写模型名称",
    )
    moderation: list[str] | None = Field(
        default_factory=list, description="内容审核模型按升序排列，在此填写模型名称"
    )


class ProviderEntity(BaseModel):
    """
    提供者实体模型类

    包含提供者的完整信息和配置
    """

    provider: str  # 提供者名称
    label: I18nObject  # 提供者标签
    description: I18nObject | None = None  # 提供者描述
    icon_small: I18nObject | None = None  # 小图标
    icon_large: I18nObject | None = None  # 大图标
    background: str | None = None  # 背景色
    help: ProviderHelpEntity | None = None  # 帮助信息
    supported_model_types: Sequence[ModelType]  # 支持的模型类型
    configurate_methods: list[ConfigurateMethod]  # 配置方法列表
    models: list[AIModelEntity] = Field(default_factory=list)  # 模型列表
    provider_credential_schema: ProviderCredentialSchema | None = None  # 提供者凭证架构
    model_credential_schema: ModelCredentialSchema | None = None  # 模型凭证架构
    position: ModelPosition | None = None  # 模型位置配置

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    def to_simple_provider(self) -> SimpleProviderEntity:
        """
        转换为简单提供者实体

        Returns:
            SimpleProviderEntity: 简化的提供者信息
        """
        return SimpleProviderEntity(
            provider=self.provider,
            label=self.label,
            icon_small=self.icon_small,
            icon_large=self.icon_large,
            supported_model_types=self.supported_model_types,
            models=self.models,
        )

    @model_validator(mode="before")
    @classmethod
    def validate_models(cls, values) -> dict:
        """
        验证并加载模型配置

        从YAML文件中加载预定义的模型配置

        Args:
            values: 原始配置值

        Returns:
            dict: 验证后的配置值

        Raises:
            ValueError: 当模型配置格式错误或文件加载失败时抛出
        """

        value = values.get("models", {})
        if isinstance(value, list):
            # 兼容从数据库反序列化回来的数据
            return values

        if not isinstance(value, dict):
            raise ValueError("models应该是一个包含模型类型配置的字典")

        cwd = os.getcwd()

        model_entities = []

        def load_models(model_type: str):
            """
            加载指定类型的模型

            Args:
                model_type: 模型类型字符串
            """
            if model_type not in value:
                return

            for path in value[model_type].get("predefined", []):
                yaml_paths = glob.glob(os.path.join(cwd, path))
                for yaml_path in yaml_paths:
                    if yaml_path.endswith("_position.yaml"):
                        if "position" not in values:
                            values["position"] = {}

                        position = load_yaml_file(yaml_path)
                        values["position"][model_type] = position
                    else:
                        model_entity = load_yaml_file(yaml_path)
                        if not model_entity:
                            raise ValueError(f"加载模型实体错误: {yaml_path}")

                        provider_model = AIModelEntity(**model_entity)
                        model_entities.append(provider_model)

        # 加载各种类型的模型
        load_models("llm")
        load_models("text_embedding")
        load_models("rerank")
        load_models("tts")
        load_models("speech2text")
        load_models("moderation")

        values["models"] = model_entities

        return values


@docs(
    description="模型提供者配置扩展",
    name="ModelProviderExtra",
)
class ModelProviderConfigurationExtra(BaseModel):
    """
    模型提供者配置扩展类

    包含提供者的额外配置信息
    """

    class Python(BaseModel):
        """
        Python相关配置

        定义Python插件的源码路径配置
        """

        provider_source: str  # 提供者源码路径
        model_sources: list[str] = Field(default_factory=list)  # 模型源码路径列表

        model_config = ConfigDict(protected_namespaces=())

    python: Python  # Python配置


@docs(
    name="ModelProvider",
    description="模型提供者配置",
    outside_reference_fields={"models": AIModelEntity},
)
class ModelProviderConfiguration(ProviderEntity):
    """
    模型提供者配置类

    继承自提供者实体，包含额外的配置信息
    """

    extra: ModelProviderConfigurationExtra  # 扩展配置


# class ProviderConfig(BaseModel):
#     """
#     提供者配置模型类（已注释）
#     """

#     provider: str
#     credentials: dict
