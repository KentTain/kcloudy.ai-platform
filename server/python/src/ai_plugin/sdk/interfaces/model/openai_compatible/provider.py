import logging

from ai_plugin.sdk.interfaces.model import ModelProvider

logger = logging.getLogger(__name__)


class OAICompatProvider(ModelProvider):
    """OpenAI兼容提供者类"""

    def validate_provider_credentials(self, credentials: dict) -> None:
        """
        验证提供者凭证（OpenAI兼容模式默认通过）

        :param credentials: 凭证字典
        """
        pass
