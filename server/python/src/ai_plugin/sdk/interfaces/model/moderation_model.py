import time
from abc import abstractmethod

from pydantic import ConfigDict

from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.interfaces.model.ai_model import AIModel


class ModerationModel(AIModel):
    """
    内容审核模型类

    提供内容审核模型的基本接口和功能实现
    """

    model_type: ModelType = ModelType.MODERATION

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    ############################################################
    #                  可由插件实现的方法                        #
    ############################################################

    @abstractmethod
    def _invoke(
        self, model: str, credentials: dict, text: str, user: str | None = None
    ) -> bool:
        """
        调用内容审核模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param text: 要审核的文本
        :param user: 唯一用户ID
        :return: 如果文本安全返回False，否则返回True
        """
        raise NotImplementedError

    ############################################################
    #                    仅供执行器使用                          #
    ############################################################

    def invoke(
        self, model: str, credentials: dict, text: str, user: str | None = None
    ) -> bool:
        """
        调用内容审核模型

        :param model: 模型名称
        :param credentials: 模型凭证
        :param text: 要审核的文本
        :param user: 唯一用户ID
        :return: 如果文本安全返回False，否则返回True
        """
        self.started_at = time.perf_counter()

        try:
            return self._invoke(model, credentials, text, user)
        except Exception as e:
            raise self._transform_invoke_error(e) from e
