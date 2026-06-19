from binascii import hexlify
from typing import IO

from ai_plugin.sdk.entities.model.speech2text import (
    Speech2TextModelConfig,
    Speech2TextResult,
)
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class Speech2TextInvocation(BackwardsInvocation[Speech2TextResult]):
    """语音转文本调用类

    用于调用ASR(Automatic Speech Recognition)模型，将语音转换为文本。
    """

    def invoke(self, model_config: Speech2TextModelConfig, file: IO[bytes]) -> str:
        """调用语音转文本模型

        Args:
            model_config: 语音转文本模型配置对象
            file: 音频文件的字节流对象

        Returns:
            识别出的文本内容

        Raises:
            Exception: 当语音转文本模型没有响应时抛出异常
        """
        # 调用后端语音转文本服务，将音频文件转换为十六进制编码
        for data in self._backwards_invoke(
            InvokeType.Speech2Text,
            Speech2TextResult,
            {
                **model_config.model_dump(),
                "file": hexlify(file.read()),  # 将音频文件内容编码为十六进制字符串
            },
        ):
            return data.result

        raise Exception("语音转文本模型没有响应")
