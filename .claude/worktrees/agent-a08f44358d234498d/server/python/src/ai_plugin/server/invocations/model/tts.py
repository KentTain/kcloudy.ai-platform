from binascii import unhexlify
from collections.abc import Generator

from ai_plugin.sdk.entities.model.tts import TTSModelConfig, TTSResult
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class TTSInvocation(BackwardsInvocation[TTSResult]):
    """文本转语音调用类

    用于调用TTS(Text-To-Speech)模型，将文本转换为语音数据。
    """

    def invoke(
        self, model_config: TTSModelConfig, content_text: str
    ) -> Generator[bytes, None, None]:
        """调用TTS模型进行文本转语音

        Args:
            model_config: TTS模型配置对象
            content_text: 需要转换的文本内容

        Yields:
            bytes: 生成的音频数据字节流
        """
        # 调用后端TTS服务，获取十六进制编码的音频数据
        for data in self._backwards_invoke(
            InvokeType.TTS,
            TTSResult,
            {
                **model_config.model_dump(),
                "content_text": content_text,
            },
        ):
            # 将十六进制字符串解码为字节数据并返回
            yield unhexlify(data.result)
