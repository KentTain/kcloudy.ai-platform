from collections.abc import Generator
from urllib.parse import urljoin

import requests

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model import (
    AIModelEntity,
    FetchFrom,
    ModelPropertyKey,
    ModelType,
)
from ai_plugin.sdk.errors.model import (
    CredentialsValidateFailedError,
    InvokeBadRequestError,
)
from ai_plugin.sdk.interfaces.model.openai_compatible.common import (
    _CommonOaiApiCompat,
)
from ai_plugin.sdk.interfaces.model.tts_model import TTSModel


class OAICompatText2SpeechModel(_CommonOaiApiCompat, TTSModel):
    """
    OpenAI兼容文本转语音模型类

    提供与OpenAI API兼容的文本转语音模型实现
    """

    def _invoke(
        self,
        model: str,
        tenant_id: str,
        credentials: dict,
        content_text: str,
        voice: str,
        user: str | None = None,
    ) -> Generator[bytes, None, None]:
        """
        调用TTS模型

        :param model: 模型名称
        :param tenant_id: 用户租户ID
        :param credentials: 模型凭证
        :param content_text: 要转换的文本内容
        :param voice: 模型音色/说话者
        :param user: 唯一用户ID
        :return: 作为字节迭代器的音频数据
        """
        # 如果提供了认证信息，设置请求头
        headers = {}
        if api_key := credentials.get("api_key"):
            headers["Authorization"] = f"Bearer {api_key}"

        # 构建端点URL
        endpoint_url = credentials.get("endpoint_url", "")
        if not endpoint_url.endswith("/"):
            endpoint_url += "/"
        endpoint_url = urljoin(endpoint_url, "audio/speech")

        # 从模型属性获取音频格式
        audio_format = self._get_model_audio_type(model, credentials)

        # 根据字数限制将文本分割成块
        word_limit = self._get_model_word_limit(model, credentials)
        sentences = self._split_text_into_sentences(content_text, word_limit or 2000)

        for sentence in sentences:
            # 准备请求载荷
            payload = {
                "model": model,
                "input": sentence,
                "voice": voice,
                "response_format": audio_format,
            }

            # 发起POST请求
            response = requests.post(
                endpoint_url, headers=headers, json=payload, stream=True
            )

            if response.status_code != 200:
                raise InvokeBadRequestError(response.text)

            # 流式传输音频数据
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        验证模型凭证

        :param model: 模型名称
        :param credentials: 模型凭证
        """
        try:
            # 获取用于验证的默认音色
            voice = self._get_model_default_voice(model, credentials)

            # 使用简单文本进行测试
            next(
                self._invoke(
                    model=model,
                    tenant_id="validate",
                    credentials=credentials,
                    content_text="Test.",
                    voice=voice,
                ),
            )
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex)) from ex

    def get_customizable_model_schema(
        self, model: str, credentials: dict
    ) -> AIModelEntity | None:
        """
        获取可自定义的模型架构

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: AI模型实体或None
        """
        # 从逗号分隔的字符串解析音色
        voice_names = credentials.get("voices", "alloy").strip().split(",")
        voices = []

        for voice in voice_names:
            voice = voice.strip()
            if not voice:
                continue

            # 为所有音色使用en-US
            voices.append(
                {
                    "name": voice,
                    "mode": voice,
                    "language": "en-US",
                },
            )

        # 如果没有提供音色或所有音色都是空字符串，使用'alloy'作为默认值
        if not voices:
            voices = [{"name": "Alloy", "mode": "alloy", "language": "en-US"}]

        return AIModelEntity(
            model=model,
            label=I18nObject(en_US=model),
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_type=ModelType.TTS,
            model_properties={
                ModelPropertyKey.AUDIO_TYPE: credentials.get("audio_type", "mp3"),
                ModelPropertyKey.WORD_LIMIT: int(credentials.get("word_limit", 4096)),
                ModelPropertyKey.DEFAULT_VOICE: voices[0]["mode"],
                ModelPropertyKey.VOICES: voices,
            },
        )

    def get_tts_model_voices(
        self, model: str, credentials: dict, language: str | None = None
    ) -> list:
        """
        重写基类的get_tts_model_voices方法以处理可自定义的音色

        :param model: 模型名称
        :param credentials: 模型凭证
        :param language: 语言（可选）
        :return: 音色列表
        """
        model_schema = self.get_customizable_model_schema(model, credentials)

        if (
            not model_schema
            or ModelPropertyKey.VOICES not in model_schema.model_properties
        ):
            raise ValueError("this model does not support voice")

        voices = model_schema.model_properties[ModelPropertyKey.VOICES]

        # 无论语言如何，始终返回所有音色
        return [{"name": d["name"], "value": d["mode"]} for d in voices]
