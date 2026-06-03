class ProviderTokenNotInitError(ValueError):
    """
    供应商令牌未初始化时引发的自定义异常
    """

    description = "供应商令牌未初始化"

    def __init__(self, *args, **kwargs):
        self.description = args[0] if args else self.description


class ProviderNotFoundError(Exception):
    """
    Provider 不存在异常

    当请求的 Provider 在系统中不存在时抛出
    """

    def __init__(self, provider: str, message: str | None = None):
        self.provider = provider
        self.message = message or f"Provider '{provider}' 不存在"
        super().__init__(self.message)


class UnsupportedProviderError(Exception):
    """
    不支持的 Provider 类型异常

    当请求的 Provider 类型不被支持时抛出
    """

    def __init__(self, provider: str, message: str | None = None):
        self.provider = provider
        self.message = message or f"不支持的 Provider 类型: '{provider}'"
        super().__init__(self.message)
