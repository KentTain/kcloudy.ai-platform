from pydantic import BaseModel, ConfigDict

from ai_plugin.sdk.entities.model import BaseModelConfig, ModelType


class ModerationModelConfig(BaseModelConfig):
    """
    内容审核模型配置类

    继承自基础模型配置，专门用于内容审核模型配置
    """

    model_type: ModelType = ModelType.MODERATION  # 模型类型，固定为内容审核

    model_config = ConfigDict(protected_namespaces=())


class ModerationResult(BaseModel):
    """
    内容审核结果模型类

    表示内容审核模型的输出结果
    """

    result: bool  # 审核结果：True表示内容安全，False表示内容有问题
