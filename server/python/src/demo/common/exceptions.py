"""
自定义异常
"""

from typing import Any


class UnauthorizedError(RuntimeError):
    """未授权异常"""

    def __init__(self, message: str = "未授权"):
        self.message = message
        super().__init__(self.message)


class ForbiddenError(RuntimeError):
    """禁止访问异常"""

    def __init__(self, message: str = "禁止访问"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(RuntimeError):
    """未找到异常"""

    def __init__(self, message: str = "未找到数据"):
        self.message = message
        super().__init__(self.message)


class BadRequestError(RuntimeError):
    """请求错误异常"""

    def __init__(self, message: str = "请求错误", data: Any | None = None):
        self.message = message
        self.data = data
        super().__init__(self.message)
