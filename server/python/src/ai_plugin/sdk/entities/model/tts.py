from pydantic import BaseModel, ConfigDict

from ai_plugin.sdk.entities.model import BaseModelConfig, ModelType


class TTSModelConfig(BaseModelConfig):
    """
    文本转语音模型配置类

    继承自基础模型配置，专门用于TTS模型配置
    """

    model_type: ModelType = ModelType.TTS  # 模型类型，固定为文本转语音
    voice: str  # 语音类型

    model_config = ConfigDict(protected_namespaces=())


class TTSResult(BaseModel):
    """
    文本转语音结果模型类

    表示TTS模型的输出结果
    """

    result: str  # 生成的音频结果（通常为base64编码或文件路径）
