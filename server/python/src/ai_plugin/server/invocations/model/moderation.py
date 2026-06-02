from ai_plugin.sdk.entities.model.moderation import (
    ModerationModelConfig,
    ModerationResult,
)
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class ModerationInvocation(BackwardsInvocation[ModerationResult]):
    """内容审核调用类

    用于调用内容审核模型，检测文本内容是否合规。
    """

    def invoke(self, model_config: ModerationModelConfig, text: str) -> bool:
        """调用内容审核模型

        Args:
            model_config: 内容审核模型配置对象
            text: 需要审核的文本内容

        Returns:
            审核结果，True表示内容合规，False表示内容违规

        Raises:
            Exception: 当内容审核模型没有响应时抛出异常
        """
        # 调用后端内容审核服务
        for data in self._backwards_invoke(
            InvokeType.Moderation,
            ModerationResult,
            {
                **model_config.model_dump(),
                "text": text,
            },
        ):
            return data.result

        raise Exception("内容审核模型没有响应")
