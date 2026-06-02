class InvokeError(Exception):
    """所有LLM异常的基类"""

    description: str | None = None

    def __init__(self, description: str | None = None) -> None:
        """
        初始化调用错误

        Args:
            description: 错误描述（可选）
        """
        super().__init__()
        if description:
            self.description = description

    def __str__(self):
        """
        返回错误的字符串表示

        Returns:
            str: 错误描述或类名
        """
        return self.description or self.__class__.__name__


class InvokeConnectionError(InvokeError):
    """当调用返回连接错误时抛出此异常"""

    description = "连接错误"


class InvokeServerUnavailableError(InvokeError):
    """当调用返回服务器不可用错误时抛出此异常"""

    description = "服务器不可用错误"


class InvokeRateLimitError(InvokeError):
    """当调用返回速率限制错误时抛出此异常"""

    description = "速率限制错误"


class InvokeAuthorizationError(InvokeError):
    """当调用返回授权错误时抛出此异常"""

    description = "提供的模型凭证不正确，请检查后重试"


class InvokeBadRequestError(InvokeError):
    """当调用返回错误请求时抛出此异常"""

    description = "错误请求"


class CredentialsValidateFailedError(Exception):
    """
    凭证验证失败错误

    当验证凭证信息失败时抛出此异常
    """

    pass
