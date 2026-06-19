class InvokeError(ValueError):
    """所有调用异常的基类"""

    description: str | None = None

    def __init__(self, description: str | None = None) -> None:
        super().__init__()
        self.description = description

    def __str__(self):
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
