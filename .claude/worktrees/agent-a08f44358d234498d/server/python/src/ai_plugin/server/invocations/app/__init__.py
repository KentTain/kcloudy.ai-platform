from collections.abc import Mapping

from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class FetchAppInvocation(BackwardsInvocation[dict]):
    """获取应用信息调用类

    用于获取应用的详细信息和元数据。
    """

    def get(
        self,
        app_id: str,
    ) -> Mapping:
        """获取应用信息

        Args:
            app_id: 应用ID

        Returns:
            包含应用信息的映射对象

        Raises:
            Exception: 当获取应用信息失败时抛出异常
        """
        response = self._backwards_invoke(
            InvokeType.FetchApp,
            dict,
            {
                "app_id": app_id,
            },
        )

        # 返回第一个响应数据
        for data in response:
            return data

        raise Exception("获取应用信息失败，没有响应")
