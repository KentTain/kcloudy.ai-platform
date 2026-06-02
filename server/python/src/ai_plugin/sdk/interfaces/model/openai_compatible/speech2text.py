from typing import IO
from urllib.parse import urljoin

import requests

from ai_plugin.sdk.errors.model import (
    CredentialsValidateFailedError,
    InvokeBadRequestError,
)
from ai_plugin.sdk.interfaces.model.openai_compatible.common import (
    _CommonOaiApiCompat,
)
from ai_plugin.sdk.interfaces.model.speech2text_model import Speech2TextModel


class OAICompatSpeech2TextModel(_CommonOaiApiCompat, Speech2TextModel):
    """
    OpenAI兼容语音转文本模型类

    提供与OpenAI API兼容的语音转文本模型实现
    """

    def _invoke(
        self, model: str, credentials: dict, file: IO[bytes], user: str | None = None
    ) -> str:
        """
        调用语音转文本模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param file: 音频文件
        :param user: 唯一用户ID
        :return: 给定音频文件的文本内容
        """
        headers = {}

        api_key = credentials.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        endpoint_url = credentials.get("endpoint_url", "https://api.openai.com/v1/")
        if not endpoint_url.endswith("/"):
            endpoint_url += "/"
        endpoint_url = urljoin(endpoint_url, "audio/transcriptions")

        payload = {"model": model}
        files = [("file", file)]
        response = requests.post(
            endpoint_url, headers=headers, data=payload, files=files
        )

        if response.status_code != 200:
            raise InvokeBadRequestError(response.text)
        response_data = response.json()
        return response_data["text"]

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        验证模型凭证

        :param model: 模型名称
        :param credentials: 模型凭证
        """
        try:
            audio_file_path = self._get_demo_file_path()

            with open(audio_file_path, "rb") as audio_file:
                self._invoke(model, credentials, audio_file)
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex)) from ex
