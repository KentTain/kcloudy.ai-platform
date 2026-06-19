from pydantic import BaseModel, ConfigDict

from ai_plugin.sdk.entities.model import BaseModelConfig, ModelType


class Speech2TextModelConfig(BaseModelConfig):
    """
    语音转文本模型配置类

    继承自基础模型配置，专门用于语音转文本模型配置
    """

    model_type: ModelType = ModelType.SPEECH2TEXT  # 模型类型，固定为语音转文本

    model_config = ConfigDict(protected_namespaces=())


class Speech2TextResult(BaseModel):
    """
    语音转文本结果模型类

    表示语音转文本模型的输出结果
    """

    result: str  # 转换后的文本结果
