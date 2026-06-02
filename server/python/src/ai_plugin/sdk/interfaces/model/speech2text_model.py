import os
from abc import abstractmethod
from typing import IO

from pydantic import ConfigDict

from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.interfaces.model.ai_model import AIModel


class Speech2TextModel(AIModel):
    """
    语音转文本模型类

    提供语音转文本模型的基本接口和功能实现
    """

    model_type: ModelType = ModelType.SPEECH2TEXT

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
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
        raise NotImplementedError

    ############################################################
    #                    仅供插件实现使用                        #
    ############################################################

    def _get_demo_file_path(self) -> str:
        """
        获取给定模型的演示文件路径

        :return: 演示文件路径
        """
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 构建音频文件的路径
        return os.path.join(current_dir, "audio.mp3")

    ############################################################
    #                    仅供执行器使用                          #
    ############################################################

    def invoke(
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
        try:
            return self._invoke(model, credentials, file, user)
        except Exception as e:
            raise self._transform_invoke_error(e) from e
