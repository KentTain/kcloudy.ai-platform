import hashlib
import logging
import re
import uuid
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from pydantic import ConfigDict

from ai_plugin.sdk.entities.model import ModelPropertyKey, ModelType
from ai_plugin.sdk.interfaces.model.ai_model import AIModel

logger = logging.getLogger(__name__)


class TTSModel(AIModel):
    """
    文本转语音模型类

    提供文本转语音模型的基本接口和功能实现
    """

    model_type: ModelType = ModelType.TTS

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
    def _invoke(
        self,
        model: str,
        tenant_id: str,
        credentials: dict,
        content_text: str,
        voice: str,
        user: str | None = None,
    ) -> bytes | Generator[bytes, None, None]:
        """
        调用文本转语音模型

        :param model: 模型名称
        :param tenant_id: 用户租户ID
        :param credentials: 模型凭证
        :param voice: 模型音色
        :param content_text: 要转换的文本内容
        :param user: 唯一用户ID
        :return: 转换后的音频文件
        """
        raise NotImplementedError

    def get_tts_model_voices(
        self, model: str, credentials: dict, language: str | None = None
    ) -> list | None:
        """
        获取给定TTS模型的音色列表

        :param language: TTS语言
        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 音色列表
        """
        model_schema = self.get_model_schema(model, credentials)

        if model_schema and ModelPropertyKey.VOICES in model_schema.model_properties:
            voices = model_schema.model_properties[ModelPropertyKey.VOICES]
            if language:
                return [
                    {"name": d["name"], "value": d["mode"]}
                    for d in voices
                    if language and language in d.get("language")
                ]
            else:
                return [{"name": d["name"], "value": d["mode"]} for d in voices]

    ############################################################
    #                    仅供插件实现使用                        #
    ############################################################

    def _get_model_default_voice(self, model: str, credentials: dict) -> Any:
        """
        获取给定TTS模型的默认音色

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 默认音色
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.DEFAULT_VOICE in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.DEFAULT_VOICE]

    def _get_model_audio_type(self, model: str, credentials: dict) -> str | None:
        """
        获取给定TTS模型的音频类型

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 音频类型
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.AUDIO_TYPE in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.AUDIO_TYPE]

    def _get_model_word_limit(self, model: str, credentials: dict) -> int | None:
        """
        获取给定TTS模型的字数限制

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 字数限制
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.WORD_LIMIT in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.WORD_LIMIT]

    def _get_model_workers_limit(self, model: str, credentials: dict) -> int | None:
        """
        获取给定TTS模型的最大工作线程数

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 最大工作线程数
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.MAX_WORKERS in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.MAX_WORKERS]

    @staticmethod
    def _split_text_into_sentences(org_text, max_length=2000, pattern=r"[。.!?]"):
        """
        将文本按句子分割

        :param org_text: 原始文本
        :param max_length: 最大长度，默认2000
        :param pattern: 分割模式，默认为句号、英文句号、感叹号、问号
        :return: 分割后的句子列表
        """
        match = re.compile(pattern)
        tx = match.finditer(org_text)
        start = 0
        result = []
        one_sentence = ""
        for i in tx:
            end = i.regs[0][1]
            tmp = org_text[start:end]
            if len(one_sentence + tmp) > max_length:
                result.append(one_sentence)
                one_sentence = ""
            one_sentence += tmp
            start = end
        last_sens = org_text[start:]
        if last_sens:
            one_sentence += last_sens
        if one_sentence != "":
            result.append(one_sentence)
        return result

    # 待办：改进流式传输功能
    @staticmethod
    def _get_file_name(file_content: str) -> str:
        """
        基于文件内容生成唯一文件名

        :param file_content: 文件内容
        :return: 生成的唯一文件名
        """
        hash_object = hashlib.sha256(file_content.encode())
        hex_digest = hash_object.hexdigest()

        namespace_uuid = uuid.UUID("a5da6ef9-b303-596f-8e88-bf8fa40f4b31")
        unique_uuid = uuid.uuid5(namespace_uuid, hex_digest)
        return str(unique_uuid)

    ############################################################
    #                    仅供执行器使用                          #
    ############################################################

    def invoke(
        self,
        model: str,
        tenant_id: str,
        credentials: dict,
        content_text: str,
        voice: str,
        user: str | None = None,
    ) -> bytes | Generator[bytes, None, None]:
        """
        调用文本转语音模型

        :param model: 模型名称
        :param tenant_id: 用户租户ID
        :param credentials: 模型凭证
        :param voice: 模型音色
        :param content_text: 要转换的文本内容
        :param user: 唯一用户ID
        :return: 转换后的音频文件
        """
        try:
            return self._invoke(
                model=model,
                tenant_id=tenant_id,
                credentials=credentials,
                user=user,
                content_text=content_text,
                voice=voice,
            )
        except Exception as e:
            raise self._transform_invoke_error(e) from e
