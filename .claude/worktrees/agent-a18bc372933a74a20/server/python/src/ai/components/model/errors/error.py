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


class ModelInvocationError(Exception):
    """
    模型调用错误

    当插件通信失败或模型调用出错时抛出
    """

    def __init__(self, message: str | None = None, original_error: Exception | None = None):
        self.message = message or "模型调用失败"
        self.original_error = original_error
        super().__init__(self.message)


class ModelTimeoutError(Exception):
    """
    模型调用超时错误

    当模型调用超时时抛出
    """

    def __init__(self, message: str | None = None, timeout: float | None = None):
        self.message = message or "模型调用超时"
        self.timeout = timeout
        super().__init__(self.message)


class ModelCredentialError(Exception):
    """
    模型凭证错误

    当模型凭证无效或缺失时抛出
    """

    def __init__(self, message: str | None = None, provider: str | None = None):
        self.message = message or "模型凭证无效"
        self.provider = provider
        super().__init__(self.message)


class ModelParameterError(Exception):
    """
    无效的模型参数异常

    当模型参数无效或缺失时抛出
    """

    def __init__(self, message: str | None = None, parameter: str | None = None):
        self.message = message or "无效的模型参数"
        self.parameter = parameter
        super().__init__(self.message)
